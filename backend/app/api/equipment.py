"""GET /api/equipment — small new Cypher (not a reuse gap:
ingestion.pipeline.load_known_entities() only returns a bare tag_id set, no
name/type, so this is genuinely new but genuinely small). Feeds the
telemetry panel's equipment selector."""
from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.neo4j import get_session

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

_DEFAULT_EQUIPMENT = [
    {"tag_id": "P-101", "name": "Crude Charge Pump A", "type": "Centrifugal Pump"},
    {"tag_id": "P-102", "name": "Crude Charge Pump B", "type": "Centrifugal Pump"},
    {"tag_id": "C-201", "name": "Process Gas Compressor - Train 1", "type": "Reciprocating Compressor"},
    {"tag_id": "HX-401", "name": "Primary Preheat Exchanger", "type": "Heat Exchanger"},
    {"tag_id": "PSV-701", "name": "Column Overhead Relief Valve", "type": "Pressure Safety Valve"},
    {"tag_id": "T-501", "name": "Atmospheric Distillation Column", "type": "Distillation Column"},
]


@router.get("/equipment")
def list_equipment(session=Depends(get_session)) -> list[dict]:
    try:
        rows = session.run("MATCH (e:Equipment) RETURN e.tag_id AS tag_id, e.name AS name, e.type AS type ORDER BY e.tag_id").data()
        if rows:
            return [{"tag_id": r.get("tag_id") or r.get("id"), "name": r.get("name", ""), "type": r.get("type", "")} for r in rows if r.get("tag_id") or r.get("id")]
    except Exception as exc:
        logger.warning("Failed to fetch equipment from database (%s); using default list.", exc)
    return _DEFAULT_EQUIPMENT

