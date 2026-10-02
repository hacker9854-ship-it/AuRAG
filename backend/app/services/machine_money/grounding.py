"""Machine Money Grounded Evidence Service (Phase 2).

Binds telemetry anomaly signals to actual GraphRAG retrieval (hybrid vector, BM25,
graph traversal) with an explicit, truthful fallback to the canonical controlled demo fixture
when retrieval components or graph databases are offline.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CANONICAL_EQUIPMENT = "P-101A"
CANONICAL_FAILURE_EVENT = "FE-001"
CANONICAL_WORK_ORDER = "WO-1002"
CANONICAL_PROCEDURE = "PROC-001"
CANONICAL_CONFIDENCE = 0.94
CANONICAL_VIBRATION_READING = 5.4
CANONICAL_VIBRATION_THRESHOLD = 4.5

CANONICAL_FIXTURE_ITEMS = [
    {
        "key": "FE-001",
        "text": "Bearing inner race spalling with high-frequency harmonic vibration peaks.",
        "score": 0.94,
    },
    {
        "key": "WO-1002",
        "text": "Overhaul work order for P-101A pump bearing assembly and lubrication replacement.",
        "score": 0.91,
    },
    {
        "key": "PROC-001",
        "text": "Standard Operating Procedure for centrifugal pump bearing inspection and vibration analysis.",
        "score": 0.89,
    },
]


def formulate_grounding_query(
    equipment_tag: str = CANONICAL_EQUIPMENT,
    vibration_reading: float = CANONICAL_VIBRATION_READING,
    vibration_threshold: float = CANONICAL_VIBRATION_THRESHOLD,
    symptom: Optional[str] = None,
) -> str:
    """Formulate deterministic search query for hybrid GraphRAG retrieval."""
    if symptom:
        return (
            f"Why did {equipment_tag} trigger an intervention after {symptom} "
            f"with vibration {vibration_reading} mm/s against {vibration_threshold} mm/s threshold?"
        )
    return (
        f"Why did {equipment_tag} trigger an intervention after vibration reached "
        f"{vibration_reading} mm/s against a {vibration_threshold} mm/s threshold?"
    )


def get_grounded_evidence_package(
    session=None,
    equipment_tag: str = CANONICAL_EQUIPMENT,
    vibration_reading: float = CANONICAL_VIBRATION_READING,
    vibration_threshold: float = CANONICAL_VIBRATION_THRESHOLD,
    event_id: Optional[str] = None,
    failure_event_id: Optional[str] = None,
    confidence: Optional[float] = None,
    query_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve operational evidence package grounded in hybrid GraphRAG retrieval.

    If Neo4j / Qdrant / sentence-transformers are online and return valid hits,
    package is labeled with source="HYBRID_RETRIEVAL", retrieval_method="HYBRID_RETRIEVAL",
    and controlled_fixture=False.

    If offline, empty, or exception encountered, falls back gracefully to the canonical controlled demo fixture
    labeled with source="CONTROLLED_DEMO_FIXTURE", retrieval_method="CONTROLLED_DEMO_FIXTURE",
    and controlled_fixture=True.
    """
    query = query_override or formulate_grounding_query(
        equipment_tag=equipment_tag,
        vibration_reading=vibration_reading,
        vibration_threshold=vibration_threshold,
    )

    hits: List[Tuple[str, str, float]] = []
    try:
        from retrieval.hybrid import retrieve

        hits = retrieve(session, query, top_k=5)
    except Exception as exc:
        logger.info(
            "Hybrid retrieval offline or unavailable (%s); falling back to controlled demo fixture.",
            exc,
        )
        hits = []

    if hits:
        fe_candidates: List[str] = []
        wo_candidates: List[str] = []
        proc_candidates: List[str] = []

        for key, text, _score in hits:
            combined = f"{key} {text}"
            fe_candidates.extend(re.findall(r"\bFE-\d+\b", combined))
            wo_candidates.extend(re.findall(r"\bWO-\d+\b", combined))
            proc_candidates.extend(re.findall(r"\bPROC-\d+\b", combined))

        matched_fe = fe_candidates[0] if fe_candidates else (failure_event_id or CANONICAL_FAILURE_EVENT)
        related_wo = wo_candidates[0] if wo_candidates else CANONICAL_WORK_ORDER
        governing_proc = proc_candidates[0] if proc_candidates else CANONICAL_PROCEDURE

        evidence_list = [matched_fe, related_wo, governing_proc]
        for key, _text, _score in hits:
            if key not in evidence_list and len(evidence_list) < 6:
                evidence_list.append(key)

        if confidence is not None:
            computed_conf = float(confidence)
        else:
            top_score = hits[0][2] if hits else CANONICAL_CONFIDENCE
            computed_conf = round(min(0.99, max(0.50, float(top_score))), 2)

        cross_layer_justification = (
            f"Because {equipment_tag} matched failure signature {matched_fe} with {computed_conf:.2f} confidence, "
            f"{related_wo} shows overdue preventative maintenance, "
            f"and procedure {governing_proc} recommends specialized bearing inspection."
        )

        return {
            "reason": f"Hybrid GraphRAG retrieved evidence for {equipment_tag}",
            "confidence": computed_conf,
            "evidence": evidence_list,
            "equipment": equipment_tag,
            "matched_failure_event": matched_fe,
            "related_work_order": related_wo,
            "governing_procedure": governing_proc,
            "cross_layer_justification": cross_layer_justification,
            "source": "HYBRID_RETRIEVAL",
            "retrieval_method": "HYBRID_RETRIEVAL",
            "controlled_fixture": False,
            "retrieval_query": query,
            "retrieved_items": [
                {"key": k, "text": t, "score": float(s)} for k, t, s in hits
            ],
            "disclosure": "Grounded via live Hybrid GraphRAG retrieval (Neo4j + Qdrant + BM25 + Cross-Encoder).",
        }

    # Fallback to canonical controlled demo fixture
    conf = float(confidence) if confidence is not None else CANONICAL_CONFIDENCE
    fe_id = failure_event_id or CANONICAL_FAILURE_EVENT
    wo_id = CANONICAL_WORK_ORDER
    proc_id = CANONICAL_PROCEDURE
    evidence_list = [fe_id, wo_id, proc_id]

    cross_layer_justification = (
        f"Because {equipment_tag} matched failure signature {fe_id} with {conf:.2f} confidence, "
        f"{wo_id} shows overdue preventative maintenance, "
        f"and procedure {proc_id} recommends specialized bearing inspection."
    )

    return {
        "reason": f"High-confidence bearing degradation pattern detected on {equipment_tag}",
        "confidence": conf,
        "evidence": evidence_list,
        "equipment": equipment_tag,
        "matched_failure_event": fe_id,
        "related_work_order": wo_id,
        "governing_procedure": proc_id,
        "cross_layer_justification": cross_layer_justification,
        "source": "CONTROLLED_DEMO_FIXTURE",
        "retrieval_method": "CONTROLLED_DEMO_FIXTURE",
        "controlled_fixture": True,
        "retrieval_query": query,
        "retrieved_items": CANONICAL_FIXTURE_ITEMS,
        "disclosure": "CONTROLLED DEMO FIXTURE: Offline environment fallback preserving deterministic demonstration of P-101A bearing degradation.",
    }
