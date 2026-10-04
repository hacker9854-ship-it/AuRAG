"""Ingest the complete real plant corpus into Qdrant vector database and verify retrieval.

Includes:
- Full incident log chunks (FE-001 to FE-007)
- Pump SOP chunks (DOC-SOP-001)
- Regulatory standards (Factories Act 1948, OISD-STD-132, ISO 10816-3)
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from retrieval.embeddings import embed_texts
from retrieval.qdrant_store import upsert_chunks, search

PLANT_CHUNKS = [
    (
        "DOC-LOG-001-C001",
        "Maintenance & Incident Log — Rampur Processing Unit. Document ID: DOC-LOG-001. Log Period: 2025-01 through 2026-01. Records plant failure events and corrective actions across Feed, Compression, Separation, Heat Recovery, and Fractionation units.",
    ),
    (
        "DOC-LOG-001-C002",
        "FE-001 — P-101 Drive-End Bearing Failure (2025-03-14). Symptom: Excessive vibration (>7 mm/s RMS) and drive-end bearing housing temperature rising above 85°C. Investigation by Rotating Equipment Engineer Ramesh Kumar traced wear to lubrication lapse. Scheduled quarterly lubrication service WO-1002 (2025-02-01) was overdue and uncompleted. Root Cause: Drive-end bearing wear caused by lubrication interval lapse per DOC-SOP-001. Corrective Action: WO-1001 replaced bearing and re-greased per OEM spec on 2025-03-15.",
    ),
    (
        "DOC-LOG-001-C003",
        "FE-002 — C-201 High Discharge Temperature Trip (2025-05-02). Symptom: Unexpected trip on high discharge temperature interlock during routine startup. Maintenance Supervisor Vikram Singh identified fouling in intercooler tubes reducing heat transfer. Root Cause: Fouled intercooler tubes caused second-stage discharge temperature to exceed trip setpoint. Corrective Action: WO-1003 cleaned intercooler tubes, reset trip, and verified explosion-prevention enclosure per Factories Act 1948 Section 37.",
    ),
    (
        "DOC-LOG-001-C004",
        "FE-003 — HX-401 Reduced Heat Recovery (2025-06-20). Symptom: Feed outlet temperature deviated gradually from design curve over 6 weeks with reduced heat recovery. Root Cause: Tube-side fouling from scale buildup past recommended cleaning interval. Corrective Action: WO-1005 chemical cleaning of tube bundle closed 2025-06-21 by Ramesh Kumar.",
    ),
    (
        "DOC-LOG-001-C005",
        "FE-004 — PSV-701 Premature Relief Event (2025-08-11). Symptom: PSV-701 mounted on vessel V-301 lifted at 90% nameplate set pressure during normal operation. Safety Officer Deepak Rao investigated: annual calibration WO-1007 was overdue and uncompleted, allowing spring fatigue and set-pressure drift to go undetected. Root Cause: Relief valve spring fatigue combined with missed calibration cycle violating OISD-STD-132 Clause 10.2(ii). Corrective Action: WO-1006 spring replacement and recalibration closed 2025-08-12.",
    ),
    (
        "DOC-LOG-001-C006",
        "FE-005 — T-501 Tower Flooding (2025-10-05). Symptom: Differential pressure across trays rose sharply above normal band; tower flooding observed. Investigation revealed post-upset inspection WO-1009 closed 2025-09-15 by Vikram Singh failed to identify tray damage from prior slug-flow event. Root Cause: Undetected tray damage from upstream slug-flow. Corrective Action: WO-1008 replaced damaged trays 12-15 closed 2025-10-06 by Ramesh Kumar.",
    ),
    (
        "DOC-LOG-001-C007",
        "FE-006 — P-102 Mechanical Seal Leak (2026-01-18). Symptom: Visible mechanical seal leak detected on standby pump P-102 during operator rounds. Root Cause: Mechanical seal degradation after exceeding rated service life without replacement per DOC-SOP-001 Section 3. Corrective Action: WO-1010 mechanical seal replacement closed 2026-01-19 by Suresh Patil.",
    ),
    (
        "DOC-LOG-001-C008",
        "FE-007 — P-101 Incipient Cavitation (2026-02-11). Symptom: Broadband vibration rose while bearing temperature remained normal during low tank level operation in tank farm TK-101. Root Cause: Suction starvation caused incipient cavitation due to violation of minimum tank level operating limit.",
    ),
    (
        "DOC-SOP-001-C001",
        "DOC-SOP-001: Centrifugal Pump Preventive Maintenance SOP v2.1 (Effective 2025-01-05). Applies to P-101 and P-102 (Feed Pumps, Train A), Unit 100 Feed Section. Defines mandatory PM tasks to prevent bearing and mechanical seal failures.",
    ),
    (
        "DOC-SOP-001-C002",
        "DOC-SOP-001 Section 3: Mandatory PM Tasks and Frequencies: Bearing lubrication (grease replenishment) - Quarterly (Maintenance Technician); Vibration RMS velocity reading - Monthly (Technician); Mechanical seal visual inspection - Monthly (Technician); Bearing housing temperature check - Weekly during operator rounds (Operator); Full bearing condition assessment - Annually (Rotating Equipment Engineer); Mechanical seal replacement - per OEM rated service life or immediately on leak detection.",
    ),
    (
        "DOC-SOP-001-C003",
        "DOC-SOP-001 Section 4: Alarm and Trip Thresholds: Bearing housing temperature: Alert at 75°C, Alarm at 85°C. Vibration RMS velocity: Alert at 4.5 mm/s, Alarm at 7.0 mm/s. Mechanical seal: any visible leakage triggers immediate work order.",
    ),
    (
        "DOC-SOP-001-C004",
        "DOC-SOP-001 Section 5: Consequence of Deferral: Skipping or delaying quarterly lubrication service is the single most common precursor to drive-end bearing wear on P-101/P-102. Grease degradation is cumulative and does not catch up on the next cycle; overdue lubrication must be flagged as an overdue work order.",
    ),
    (
        "DOC-REG-001-S31",
        "Factories Act 1948 Section 31 (Pressure Plant Safety): If in any factory plant or machinery operates at a pressure above atmospheric pressure, effective measures shall be taken to ensure the safe working pressure is not exceeded. Applies to pressure vessel V-301 and safety valve PSV-701.",
    ),
    (
        "DOC-REG-001-S37",
        "Factories Act 1948 Section 37 (Explosion and Flammable Atmosphere Prevention): Where manufacturing produces flammable gas, vapour, or dust likely to explode, all practicable measures shall be taken by effective enclosure, removal of accumulation, and exclusion of ignition sources. Applies to compressors C-201, C-202, and reactor R-601.",
    ),
    (
        "DOC-REG-002-102",
        "OISD-STD-132 Clause 10.2(ii): The Testing and Maintenance History of the Safety Relief Valve must be provided to the in-house testing team prior to testing or calibration. Applies to PSV-701.",
    ),
    (
        "DOC-REG-002-MED",
        "OISD-STD-132 Testing Medium: Water, air or an inert gas such as bottled nitrogen is recommended for pressure testing of Safety Relief Valves; hydrocarbon or natural gas shall not be used as test medium.",
    ),
    (
        "DOC-REG-003-ISO",
        "ISO 10816-3 Mechanical Vibration Severity Standard: Class II industrial rotating machines exceeding 4.5 mm/s RMS vibration velocity breach Zone B into Zone C (unsatisfactory continuous operation; mandatory corrective maintenance). Exceeding 7.0 mm/s reaches Zone D (immediate damage/trip risk).",
    ),
]


def ingest():
    print(f"Embedding {len(PLANT_CHUNKS)} real plant chunks with FastEmbed...")
    texts = [text for _, text in PLANT_CHUNKS]
    vectors = embed_texts(texts)
    items = [(cid, vec, text) for (cid, text), vec in zip(PLANT_CHUNKS, vectors)]

    print(f"Upserting {len(items)} chunks into Qdrant collection 'chunks'...")
    upsert_chunks(items)
    print("Upsert complete!")

    # Verify search
    test_query = "Why did P-101 bearing fail?"
    query_vec = embed_texts([test_query])[0]
    hits = search(query_vec, top_k=3)
    print(f"\nVerification search for: {test_query!r}")
    for cid, text, score in hits:
        print(f"  [{score:.4f}] {cid}: {text[:75]}...")


if __name__ == "__main__":
    ingest()
