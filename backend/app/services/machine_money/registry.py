"""Demo Service Registry and Idempotency key generator for Machine Money (Sections 12 & 14).

Explicitly labeled as 'Demo Service Registry [MOCK / SIMULATION]' per Bitshala BOSS Battle guidelines.
"""
import hashlib
from typing import Any, Dict, List, Optional
from backend.app.services.machine_money.schemas import ServiceDefinition

REGISTRY_LABEL = "Demo Service Registry [MOCK / SIMULATION]"

DEMO_SERVICES: List[Dict[str, Any]] = [
    {
        "service_id": "bearing-inspection",
        "name": "High-Frequency Vibration & Ultrasound Bearing Diagnostic",
        "provider_id": "maintenance-node-a",
        "provider_name": "Industrial Dynamics Specialist Node A",
        "price_sats": 250,
        "equipment_class": "pump",
        "description": "Autonomous acoustic emission analysis and FFT spectral peak detection for high-criticality bearings.",
        "estimated_duration_hours": 1.5,
        "parts_included": ["synthetic_ester_lubricant_sample", "sensor_coupling_pad"],
        "is_mock": True,
    },
    {
        "service_id": "thermal-diagnostics",
        "name": "Infrared Thermal Gradient Scan & Heat Exchanger Assessment",
        "provider_id": "diagnostic-node-b",
        "provider_name": "SpectraThermal Telemetry Node B",
        "price_sats": 150,
        "equipment_class": "heat_exchanger",
        "description": "FLIR thermographic baseline differential scan to detect tube bundle fouling or hot-spots.",
        "estimated_duration_hours": 1.0,
        "parts_included": ["thermal_calibration_target"],
        "is_mock": True,
    },
    {
        "service_id": "oil-tribology-analysis",
        "name": "ISO 4406 Lubrication Particle Contamination Analysis",
        "provider_id": "tribology-node-c",
        "provider_name": "Precision Tribology Dispatch Node C",
        "price_sats": 100,
        "equipment_class": "compressor",
        "description": "Spectrometric oil analysis (ferrography) verifying viscosity index, water ppm, and wear metals.",
        "estimated_duration_hours": 2.0,
        "parts_included": ["sampling_bottle_kit", "optical_particle_count_slide"],
        "is_mock": True,
    },
    {
        "service_id": "laser-shaft-alignment",
        "name": "Dynamic Shaft & Coupling Laser Alignment",
        "provider_id": "alignment-node-d",
        "provider_name": "OpticAlign Robotic Systems Node D",
        "price_sats": 400,
        "equipment_class": "turbine",
        "description": "Dual-beam laser alignment correcting angular and parallel soft-foot offset under thermal growth.",
        "estimated_duration_hours": 3.0,
        "parts_included": ["stainless_shim_assortment_316L", "flex_coupling_insert"],
        "is_mock": True,
    },
    {
        "service_id": "valve-integrity-test",
        "name": "Emergency Relief Valve Seat Leakage & Set-Pressure Recalibration",
        "provider_id": "valve-node-e",
        "provider_name": "FlowGuard Pressure Safety Node E",
        "price_sats": 300,
        "equipment_class": "relief_valve",
        "description": "API 527 bubble test and electronic seat-tightness telemetry certification.",
        "estimated_duration_hours": 2.5,
        "parts_included": ["resilient_o_ring_kalrez", "tamper_proof_lead_seal"],
        "is_mock": True,
    },
]


def generate_idempotency_key(
    site_id: str,
    equipment_id: str,
    service_id: str,
    predictive_event_id: str,
) -> str:
    """Generate deterministic SHA-256 idempotency key ensuring repeated predictive alerts
    cannot trigger duplicate financial settlement.
    """
    raw = f"{site_id}:{equipment_id}:{service_id}:{predictive_event_id}".strip().lower()
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"idemp-{digest}"


def list_services(equipment_class: Optional[str] = None) -> List[ServiceDefinition]:
    """Return all catalog services in the demo registry, optionally filtered by equipment category."""
    services = []
    for item in DEMO_SERVICES:
        if equipment_class and item["equipment_class"].lower() != equipment_class.lower():
            continue
        services.append(ServiceDefinition(**item))
    return services


def get_service(service_id: str) -> Optional[ServiceDefinition]:
    """Retrieve service specifications by unique service_id."""
    for item in DEMO_SERVICES:
        if item["service_id"].lower() == service_id.lower():
            return ServiceDefinition(**item)
    return None


def get_provider_registry_info() -> Dict[str, Any]:
    """Expose full catalog with audit transparency disclosures."""
    services = list_services()
    providers = {}
    for s in services:
        if s.provider_id not in providers:
            providers[s.provider_id] = {
                "provider_id": s.provider_id,
                "provider_name": s.provider_name,
                "supported_services": [],
                "network": "lightning-regtest",
                "status": "ONLINE",
            }
        providers[s.provider_id]["supported_services"].append(s.service_id)

    return {
        "registry_title": REGISTRY_LABEL,
        "disclosure": "Deterministic service registry for autonomous machine-to-machine demonstration under BOSS Battle rules.",
        "total_services": len(services),
        "total_providers": len(providers),
        "providers": list(providers.values()),
        "services": [s.model_dump() for s in services],
    }
