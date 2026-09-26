"""Continuous synthetic telemetry worker that emits durable warnings."""

import os
import time
from datetime import datetime, timedelta, timezone

from backend.app.services.events import create_predictive_event, publish_event


def _now() -> datetime:
    return datetime.now(timezone.utc)


def scan_equipment(session, equipment_tag: str, drift_pct: float) -> dict:
    from telemetry.draft import build_warning
    from telemetry.generator import generate_reading
    from telemetry.pattern_match import match_reading

    reading = generate_reading(
        session,
        equipment_tag,
        drift_pct=drift_pct,
    )
    matches = match_reading(session, equipment_tag, reading)
    return {
        "equipment": equipment_tag,
        "reading": reading,
        "warning": build_warning(equipment_tag, matches),
    }


class TelemetryWorker:
    def __init__(
        self,
        *,
        equipment_tags: list[str],
        scan_fn=scan_equipment,
        create_fn=create_predictive_event,
        publish_fn=publish_event,
        now=_now,
        cooldown: timedelta = timedelta(minutes=30),
        drift_schedule: list[float] | None = None,
    ):
        self.equipment_tags = equipment_tags
        self.scan_fn = scan_fn
        self.create_fn = create_fn
        self.publish_fn = publish_fn
        self.now = now
        self.cooldown = cooldown
        self.drift_schedule = drift_schedule or [0.0, 0.25, 0.5, 0.75, 1.0]
        self._phase = 0

    def run_cycle(self, session) -> dict:
        drift_pct = self.drift_schedule[self._phase % len(self.drift_schedule)]
        self._phase += 1
        created = 0
        deduplicated = 0
        scans = []

        for equipment_tag in self.equipment_tags:
            scan = self.scan_fn(session, equipment_tag, drift_pct)
            scans.append(scan)
            warning = scan.get("warning")
            if not warning:
                continue

            failure_event_id = warning["matched_failure_event"]
            current = self.now()
            event = self.create_fn(
                session,
                equipment_tag=equipment_tag,
                failure_event_id=failure_event_id,
                similarity=warning["similarity"],
                symptom=warning["symptom"],
                reading=scan["reading"],
                detected_at=current.isoformat(),
                cooldown_seconds=max(int(self.cooldown.total_seconds()), 1),
            )
            if event.get("_created", True):
                self.publish_fn(event["id"])
                created += 1
            else:
                deduplicated += 1

        return {
            "drift_pct": drift_pct,
            "equipment_scanned": len(self.equipment_tags),
            "events_created": created,
            "deduplicated": deduplicated,
            "scans": scans,
        }


def main() -> None:
    from retrieval.index_chunks import get_database, get_driver

    equipment_tags = [
        tag.strip()
        for tag in os.environ.get(
            "TELEMETRY_EQUIPMENT_TAGS",
            "P-101,C-201,HX-401,PSV-701,T-501,P-102",
        ).split(",")
        if tag.strip()
    ]
    interval = max(float(os.environ.get("TELEMETRY_INTERVAL_SECONDS", "15")), 1.0)
    worker = TelemetryWorker(equipment_tags=equipment_tags)
    driver = get_driver()
    database = get_database()

    print(
        f"Telemetry worker active for {len(equipment_tags)} equipment tags "
        f"at {interval:.1f}s intervals."
    )
    while True:
        with driver.session(database=database) as session:
            result = worker.run_cycle(session)
        print(
            f"telemetry drift={result['drift_pct']:.2f} "
            f"events={result['events_created']} "
            f"deduplicated={result['deduplicated']}"
        )
        time.sleep(interval)


if __name__ == "__main__":
    main()
