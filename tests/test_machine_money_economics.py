"""Unit and integration tests for Task 5.2: Industrial Economics model and transparent plant assumptions."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.machine_money.economics import (
    CALCULATION_VERSION,
    ESTIMATED_MARKER,
    calculate_industrial_economics,
    get_plant_assumptions,
)
from backend.app.services.machine_money.schemas import (
    IndustrialEconomicsModel,
    IndustrialEconomicsRequest,
    IndustrialPlantAssumptions,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_economics_baseline_p101a_calculation():
    """Task 5.2 / FR-14: Verify default P-101A downtime exposure, intervention cost, and transparent formulas."""
    model = calculate_industrial_economics(IndustrialEconomicsRequest(equipment_tag="P-101A"))

    assert isinstance(model, IndustrialEconomicsModel)
    assert model.is_estimated is True
    assert model.estimated_marker == ESTIMATED_MARKER
    assert model.calculation_version == CALCULATION_VERSION
    assert model.equipment_tag == "P-101A"

    # Downtime hours and hourly cost
    assert model.downtime_hours_avoided == 4.5
    assert model.hourly_downtime_cost_usd == 260000.0

    # Downtime exposure: 4.5 * 260,000 = $1,170,000.00
    assert model.estimated_downtime_exposure_usd == 1170000.0

    # Risk-weighted exposure (85% catastrophic failure probability): 1,170,000 * 0.85 = $994,500.00
    assert model.risk_weighted_exposure_usd == 994500.0

    # Intervention cost: 250 sats at $65,000/BTC ($0.00065/sat) = $0.1625
    assert model.intervention_cost_sats == 250
    assert model.intervention_cost_usd == 0.1625

    # Net value preserved: 1,170,000 - 0.1625 = $1,169,999.84
    assert model.net_value_preserved_usd == 1169999.84

    # Protection multiple (ROI ratio): > 7 million x
    assert model.protection_multiple > 7000000.0

    # Lead time saved: 4.2h manual PO procurement vs 2.1s autonomous M2M dispatch
    assert model.lead_time_saved_hours == 4.2

    # Formulas and inspectable metadata
    assert "Avoided Downtime Hours" in model.formula
    assert "Synthetic plant model" in model.data_basis
    assert len(model.transparency_notes) > 20


def test_assumptions_stored_separately():
    """Task 5.2: Requirements check - assumptions stored separately and versioned."""
    # Check P-101A
    p101 = get_plant_assumptions("P-101A")
    assert isinstance(p101, IndustrialPlantAssumptions)
    assert p101.equipment_tag == "P-101A"
    assert p101.hourly_downtime_cost_usd == 260000.0
    assert p101.unmitigated_downtime_hours == 4.5
    assert p101.assumptions_version == "2026.1-synthetic-p101a"

    # Check K-201
    k201 = get_plant_assumptions("K-201")
    assert isinstance(k201, IndustrialPlantAssumptions)
    assert k201.equipment_tag == "K-201"
    assert k201.hourly_downtime_cost_usd == 320000.0
    assert k201.unmitigated_downtime_hours == 6.0
    assert k201.assumptions_version == "2026.1-synthetic-k201"

    # Check T-301
    t301 = get_plant_assumptions("T-301")
    assert isinstance(t301, IndustrialPlantAssumptions)
    assert t301.equipment_tag == "T-301"
    assert t301.hourly_downtime_cost_usd == 195000.0


def test_economics_custom_parameter_overrides():
    """Verify custom parameter overrides for user-driven sensitivity analysis."""
    req = IndustrialEconomicsRequest(
        equipment_tag="P-101A",
        intervention_cost_sats=500,
        hourly_downtime_cost_usd=100000.0,
        unmitigated_downtime_hours=2.0,
    )
    res = calculate_industrial_economics(req)

    assert res.estimated_downtime_exposure_usd == 200000.0  # 2.0 * $100k
    assert res.intervention_cost_sats == 500
    assert res.intervention_cost_usd == 500 * 0.00065  # $0.325
    assert res.net_value_preserved_usd == round(200000.0 - 0.325, 2)



def test_economics_api_endpoints(client):
    """Verify BE-05 API routes: GET /analytics/economics, POST /analytics/economics, and GET /analytics/assumptions/{tag}."""
    # 1. GET /analytics/economics
    get_res = client.get("/api/machine-money/analytics/economics?equipment_tag=P-101A")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["equipment_tag"] == "P-101A"
    assert data["estimated_downtime_exposure_usd"] == 1170000.0
    assert data["is_estimated"] is True
    assert data["estimated_marker"] == "ESTIMATED_SYNTHETIC_MODEL"
    assert "formula" in data
    assert "assumptions" in data

    # 2. POST /analytics/economics
    post_res = client.post(
        "/api/machine-money/analytics/economics",
        json={"equipment_tag": "K-201", "intervention_cost_sats": 400},
    )
    assert post_res.status_code == 200
    p_data = post_res.json()
    assert p_data["equipment_tag"] == "K-201"
    assert p_data["estimated_downtime_exposure_usd"] == 6.0 * 320000.0

    # 3. GET /analytics/assumptions/{equipment_tag}
    assump_res = client.get("/api/machine-money/analytics/assumptions/P-101A")
    assert assump_res.status_code == 200
    a_data = assump_res.json()
    assert a_data["equipment_tag"] == "P-101A"
    assert a_data["hourly_downtime_cost_usd"] == 260000.0
    assert a_data["unmitigated_downtime_hours"] == 4.5
