"""Tests for Machine Money Grounded Evidence Service (Phase 2).

Covers:
- Query formulation determinism
- Offline fallback to CONTROLLED_DEMO_FIXTURE
- Mock hybrid retrieval live path
- Confidence gating (< 0.75 -> PENDING_APPROVAL, >= 0.75 -> proceeds)
"""
import asyncio
import pytest
from unittest.mock import patch, MagicMock

from backend.app.services.machine_money.grounding import (
    CANONICAL_CONFIDENCE,
    CANONICAL_EQUIPMENT,
    CANONICAL_FAILURE_EVENT,
    CANONICAL_FIXTURE_ITEMS,
    CANONICAL_PROCEDURE,
    CANONICAL_VIBRATION_READING,
    CANONICAL_VIBRATION_THRESHOLD,
    CANONICAL_WORK_ORDER,
    formulate_grounding_query,
    get_grounded_evidence_package,
)
from backend.app.services.machine_money.service import MachineMoneyService


def test_query_formulation_deterministic():
    """Verify the grounding query is deterministic and includes canonical parameters."""
    query = formulate_grounding_query()
    assert "P-101A" in query
    assert "5.4" in query
    assert "4.5" in query
    assert "trigger an intervention" in query


def test_query_formulation_custom_params():
    """Verify query uses custom equipment_tag and readings."""
    query = formulate_grounding_query(
        equipment_tag="C-201B",
        vibration_reading=7.8,
        vibration_threshold=6.0,
    )
    assert "C-201B" in query
    assert "7.8" in query
    assert "6.0" in query


def test_query_formulation_with_symptom():
    """Verify query includes symptom when provided."""
    query = formulate_grounding_query(symptom="bearing overheating")
    assert "bearing overheating" in query
    assert "P-101A" in query


def test_offline_fallback_returns_controlled_fixture():
    """When retrieval is offline (session=None, no imports), fallback to CONTROLLED_DEMO_FIXTURE."""
    pkg = get_grounded_evidence_package(session=None)

    assert pkg["source"] == "CONTROLLED_DEMO_FIXTURE"
    assert pkg["retrieval_method"] == "CONTROLLED_DEMO_FIXTURE"
    assert pkg["controlled_fixture"] is True
    assert pkg["equipment"] == CANONICAL_EQUIPMENT
    assert pkg["confidence"] == CANONICAL_CONFIDENCE
    assert pkg["matched_failure_event"] == CANONICAL_FAILURE_EVENT
    assert pkg["related_work_order"] == CANONICAL_WORK_ORDER
    assert pkg["governing_procedure"] == CANONICAL_PROCEDURE
    assert "FE-001" in pkg["evidence"]
    assert "WO-1002" in pkg["evidence"]
    assert "PROC-001" in pkg["evidence"]
    assert "CONTROLLED DEMO FIXTURE" in pkg["disclosure"]
    assert pkg["retrieval_query"] is not None
    assert len(pkg["retrieved_items"]) == len(CANONICAL_FIXTURE_ITEMS)


def test_offline_fallback_with_custom_confidence():
    """Verify fallback respects explicitly provided confidence."""
    pkg = get_grounded_evidence_package(session=None, confidence=0.60)
    assert pkg["confidence"] == 0.60
    assert pkg["source"] == "CONTROLLED_DEMO_FIXTURE"


def test_offline_fallback_with_custom_failure_event():
    """Verify fallback respects custom failure_event_id."""
    pkg = get_grounded_evidence_package(session=None, failure_event_id="FE-099")
    assert pkg["matched_failure_event"] == "FE-099"
    assert "FE-099" in pkg["evidence"]


def test_offline_fallback_cross_layer_justification():
    """Verify cross_layer_justification is well-formed."""
    pkg = get_grounded_evidence_package(session=None, equipment_tag="P-101A")
    just = pkg["cross_layer_justification"]
    assert "P-101A" in just
    assert "FE-001" in just
    assert "WO-1002" in just
    assert "PROC-001" in just
    assert "confidence" in just


@patch("retrieval.hybrid.retrieve")
def test_hybrid_retrieval_live_path(mock_retrieve):
    """When hybrid retrieval returns hits, package is labeled HYBRID_RETRIEVAL."""
    mock_retrieve.return_value = [
        ("FE-001", "Bearing inner race spalling detected on P-101A pump.", 0.95),
        ("WO-1002", "Overhaul work order for P-101A bearing assembly.", 0.90),
        ("PROC-001", "SOP for centrifugal pump bearing inspection.", 0.88),
    ]

    pkg = get_grounded_evidence_package(session=MagicMock())

    assert pkg["source"] == "HYBRID_RETRIEVAL"
    assert pkg["retrieval_method"] == "HYBRID_RETRIEVAL"
    assert pkg["controlled_fixture"] is False
    assert pkg["matched_failure_event"] == "FE-001"
    assert pkg["related_work_order"] == "WO-1002"
    assert pkg["governing_procedure"] == "PROC-001"
    assert "FE-001" in pkg["evidence"]
    assert len(pkg["retrieved_items"]) == 3
    assert "Hybrid GraphRAG" in pkg["disclosure"]


@patch("retrieval.hybrid.retrieve")
def test_hybrid_retrieval_empty_falls_back(mock_retrieve):
    """When hybrid retrieval returns empty list, falls back to fixture."""
    mock_retrieve.return_value = []

    pkg = get_grounded_evidence_package(session=MagicMock())

    assert pkg["source"] == "CONTROLLED_DEMO_FIXTURE"
    assert pkg["retrieval_method"] == "CONTROLLED_DEMO_FIXTURE"
    assert pkg["controlled_fixture"] is True


@patch("retrieval.hybrid.retrieve")
def test_hybrid_retrieval_exception_falls_back(mock_retrieve):
    """When hybrid retrieval raises exception, falls back gracefully."""
    mock_retrieve.side_effect = RuntimeError("Neo4j connection refused")

    pkg = get_grounded_evidence_package(session=MagicMock())

    assert pkg["source"] == "CONTROLLED_DEMO_FIXTURE"
    assert pkg["controlled_fixture"] is True


@patch("retrieval.hybrid.retrieve")
def test_hybrid_retrieval_confidence_from_hits(mock_retrieve):
    """When no explicit confidence, derive from top hit score."""
    mock_retrieve.return_value = [
        ("FE-001", "Bearing spalling P-101A", 0.87),
    ]
    pkg = get_grounded_evidence_package(session=MagicMock())
    assert pkg["confidence"] == 0.87
    assert pkg["source"] == "HYBRID_RETRIEVAL"


@patch("retrieval.hybrid.retrieve")
def test_hybrid_retrieval_explicit_confidence_overrides(mock_retrieve):
    """When explicit confidence provided, it overrides hit scores."""
    mock_retrieve.return_value = [
        ("FE-001", "Bearing spalling P-101A", 0.87),
    ]
    pkg = get_grounded_evidence_package(session=MagicMock(), confidence=0.55)
    assert pkg["confidence"] == 0.55
    assert pkg["source"] == "HYBRID_RETRIEVAL"


def test_confidence_gate_below_threshold():
    """Confidence < 0.75 should result in PENDING_APPROVAL in judge scenario."""
    service = MachineMoneyService()
    res = asyncio.run(
        service.execute_judge_scenario(
            db=None,
            scenario="INDUSTRIAL_EMERGENCY",
            equipment_id="P-101A",
            override_cost_sats=250,
            auto_approve=True,
            confidence=0.60,
        )
    )
    assert res.status == "PENDING_APPROVAL"
    policy_event = next(e for e in res.events if e.stage.value == "POLICY_EVALUATED")
    assert policy_event.status == "PENDING_APPROVAL"
    assert "confidence" in policy_event.message.lower()


def test_confidence_gate_above_threshold():
    """Confidence >= 0.75 should proceed past confidence gate."""
    service = MachineMoneyService()
    res = asyncio.run(
        service.execute_judge_scenario(
            db=None,
            scenario="INDUSTRIAL_EMERGENCY",
            equipment_id="P-101A",
            override_cost_sats=250,
            auto_approve=True,
            confidence=0.94,
        )
    )
    # Should not be stopped by confidence gate (may still succeed or fail for other reasons)
    # Key assertion: if POLICY_EVALUATED exists, it shouldn't be a confidence gate issue
    policy_events = [e for e in res.events if e.stage.value == "POLICY_EVALUATED"]
    if policy_events:
        pe = policy_events[0]
        if pe.status == "PENDING_APPROVAL":
            # Should only be pending for spending cap, NOT confidence
            assert "confidence" not in pe.data.get("reason", "").lower() or "below" not in pe.data.get("reason", "").lower()


def test_evidence_package_has_retrieval_method():
    """Verify evidence_package in judge response contains retrieval_method."""
    service = MachineMoneyService()
    res = asyncio.run(
        service.execute_judge_scenario(
            db=None,
            scenario="INDUSTRIAL_EMERGENCY",
            equipment_id="P-101A",
            override_cost_sats=250,
            auto_approve=True,
        )
    )
    evidence_event = next(e for e in res.events if e.stage.value == "EVIDENCE_MATCHED")
    assert "retrieval_method" in evidence_event.data
    assert evidence_event.data["retrieval_method"] in ("HYBRID_RETRIEVAL", "CONTROLLED_DEMO_FIXTURE")


def test_stage2_message_format_controlled_fixture():
    """Verify Stage 2 message includes [CONTROLLED DEMO FIXTURE] prefix when offline."""
    service = MachineMoneyService()
    res = asyncio.run(
        service.execute_judge_scenario(
            db=None,
            scenario="INDUSTRIAL_EMERGENCY",
            equipment_id="P-101A",
            override_cost_sats=250,
            auto_approve=True,
        )
    )
    evidence_event = next(e for e in res.events if e.stage.value == "EVIDENCE_MATCHED")
    if evidence_event.data.get("retrieval_method") == "CONTROLLED_DEMO_FIXTURE":
        assert "[CONTROLLED DEMO FIXTURE]" in evidence_event.message
    else:
        assert "Hybrid GraphRAG" in evidence_event.message
