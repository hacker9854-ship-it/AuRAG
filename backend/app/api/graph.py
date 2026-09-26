"""Resolve cited evidence into a bounded, connected answer-trail subgraph."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.neo4j import get_session

router = APIRouter()

_ID_PROPERTY = {
    "Equipment": "tag_id",
    "RegulatoryClause": "clause_id",
    "Person": "name",
}
_KNOWN_TYPES = {
    "Equipment",
    "RegulatoryClause",
    "Person",
    "FailureEvent",
    "WorkOrder",
    "Procedure",
    "Chunk",
    "Document",
}
_EXCLUDED_PROPS = {"embedding"}
_PATH_HOPS = 4
_NEIGHBOR_HOPS = 2


class GraphNode(BaseModel):
    type: str
    id: str


class GraphRequest(BaseModel):
    graph_paths: list[GraphNode]


def _fetch_node(session, node_type: str, node_id: str) -> dict | None:
    if node_type not in _KNOWN_TYPES:
        return None
    prop = _ID_PROPERTY.get(node_type, "id")
    row = session.run(
        f"MATCH (n:{node_type} {{{prop}: $val}}) "
        "RETURN elementId(n) AS eid, properties(n) AS props",
        val=node_id,
    ).single()
    if not row:
        return None
    props = {
        key: value
        for key, value in row["props"].items()
        if key not in _EXCLUDED_PROPS
    }
    return {
        "eid": row["eid"],
        "id": f"{node_type}:{node_id}",
        "type": node_type,
        "properties": props,
    }


def _node_id(node_type: str, props: dict, eid: str) -> str:
    prop = _ID_PROPERTY.get(node_type, "id")
    value = props.get(prop)
    return f"{node_type}:{value if value is not None else eid}"


def _shape_path_node(raw: dict) -> dict | None:
    labels = [label for label in raw.get("labels", []) if label in _KNOWN_TYPES]
    if not labels:
        return None
    node_type = labels[0]
    props = {
        key: value
        for key, value in (raw.get("props") or {}).items()
        if key not in _EXCLUDED_PROPS
    }
    eid = raw["eid"]
    return {
        "eid": eid,
        "id": _node_id(node_type, props, eid),
        "type": node_type,
        "properties": props,
    }


def _merge_path_rows(
    rows: list[dict],
    nodes_by_eid: dict[str, dict],
    relationships_by_key: dict[tuple, dict],
) -> None:
    for row in rows:
        for raw_node in row.get("path_nodes") or []:
            node = _shape_path_node(raw_node)
            if node is not None:
                nodes_by_eid[node["eid"]] = node

        for raw_relationship in row.get("path_relationships") or []:
            source_eid = raw_relationship.get("source")
            target_eid = raw_relationship.get("target")
            if source_eid not in nodes_by_eid or target_eid not in nodes_by_eid:
                continue
            source = nodes_by_eid[source_eid]["id"]
            target = nodes_by_eid[target_eid]["id"]
            rel_type = raw_relationship.get("type")
            key = tuple(sorted((source, target))) + (rel_type,)
            relationships_by_key[key] = {
                "source": source,
                "target": target,
                "type": rel_type,
            }


def _path_projection() -> str:
    return """
        RETURN
          [n IN nodes(p) | {
            eid: elementId(n),
            labels: labels(n),
            props: properties(n)
          }] AS path_nodes,
          [r IN relationships(p) | {
            source: elementId(startNode(r)),
            target: elementId(endNode(r)),
            type: type(r)
          }] AS path_relationships
    """


@router.post("/graph")
def fetch_graph(request: GraphRequest, session=Depends(get_session)) -> dict:
    try:
        nodes_by_eid: dict[str, dict] = {}
        for graph_node in request.graph_paths:
            node = _fetch_node(session, graph_node.type, graph_node.id)
            if node is not None:
                nodes_by_eid[node["eid"]] = node

        relationships_by_key: dict[tuple, dict] = {}
        eids = list(nodes_by_eid)

        if len(eids) >= 2:
            rows = session.run(
                f"""
                UNWIND $eids AS source_eid
                UNWIND $eids AS target_eid
                WITH source_eid, target_eid
                WHERE source_eid < target_eid
                MATCH (source), (target)
                WHERE elementId(source) = source_eid
                  AND elementId(target) = target_eid
                MATCH p = shortestPath((source)-[*..{_PATH_HOPS}]-(target))
                {_path_projection()}
                LIMIT 30
                """,
                eids=eids,
            ).data()
            _merge_path_rows(rows, nodes_by_eid, relationships_by_key)

        # A single citation has no pair to connect, and two citations can be
        # outside the bounded path. Add a small deterministic neighborhood so
        # each evidence node still shows its factual graph attachments.
        rows = (
            session.run(
                f"""
                UNWIND $eids AS source_eid
                MATCH (source)
                WHERE elementId(source) = source_eid
                MATCH p = (source)-[*1..{_NEIGHBOR_HOPS}]-(neighbor)
                WITH p, neighbor
                ORDER BY length(p), elementId(neighbor)
                LIMIT 40
                {_path_projection()}
                """,
                eids=eids,
            ).data()
            if eids
            else []
        )
        _merge_path_rows(rows, nodes_by_eid, relationships_by_key)

        return {
            "nodes": [
                {
                    key: value
                    for key, value in node.items()
                    if key != "eid"
                }
                for node in nodes_by_eid.values()
            ],
            "relationships": list(relationships_by_key.values()),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "graph_failed", "detail": str(exc)},
        ) from exc
