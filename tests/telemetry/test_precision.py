import json

from telemetry.draft import _CONFIDENCE_FLOOR
from telemetry.pattern_match import match_reading


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def data(self):
        return self.rows


class _Session:
    def run(self, _query, **_params):
        return _Result(
            [
                {
                    "id": "FE-BEARING",
                    "sig": json.dumps(
                        {"vibration_mm_s": 7.5, "bearing_temp_c": 87}
                    ),
                    "symptom": "hot bearing",
                    "root_cause": "wear",
                },
                {
                    "id": "FE-CAVITATION",
                    "sig": json.dumps(
                        {"vibration_mm_s": 6.8, "bearing_temp_c": 60}
                    ),
                    "symptom": "cavitation",
                    "root_cause": "suction starvation",
                },
            ]
        )


def test_overlapping_same_equipment_failure_modes_are_discriminated():
    session = _Session()

    bearing = match_reading(
        session,
        "P-101",
        {"vibration_mm_s": 7.5, "bearing_temp_c": 87},
    )
    cavitation = match_reading(
        session,
        "P-101",
        {"vibration_mm_s": 6.8, "bearing_temp_c": 60},
    )
    healthy = match_reading(
        session,
        "P-101",
        {"vibration_mm_s": 2.0, "bearing_temp_c": 55},
    )

    assert bearing[0]["failure_event_id"] == "FE-BEARING"
    assert bearing[0]["similarity"] >= _CONFIDENCE_FLOOR
    assert cavitation[0]["failure_event_id"] == "FE-CAVITATION"
    assert cavitation[0]["similarity"] >= _CONFIDENCE_FLOOR
    assert healthy[0]["similarity"] < _CONFIDENCE_FLOOR
