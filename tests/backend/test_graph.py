from backend.app.api.graph import GraphNode, GraphRequest, fetch_graph


class _Result:
    def __init__(self, *, record=None, rows=None):
        self._record = record
        self._rows = rows or []

    def single(self):
        return self._record

    def data(self):
        return self._rows


class _Session:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        return self.results.pop(0)


def _path(nodes, relationships):
    return _Result(
        rows=[
            {
                "path_nodes": nodes,
                "path_relationships": relationships,
            }
        ]
    )


def test_graph_expands_intermediate_nodes_between_citations():
    failure = {
        "eid": "1",
        "labels": ["FailureEvent"],
        "props": {"id": "FE-001", "root_cause": "wear"},
    }
    equipment = {
        "eid": "2",
        "labels": ["Equipment"],
        "props": {"tag_id": "P-101", "name": "Feed pump"},
    }
    work_order = {
        "eid": "3",
        "labels": ["WorkOrder"],
        "props": {"id": "WO-1002", "status": "Closed"},
    }
    procedure = {
        "eid": "4",
        "labels": ["Procedure"],
        "props": {"id": "PROC-001", "title": "Lubrication"},
    }
    session = _Session(
        [
            _Result(record={"eid": "1", "props": failure["props"]}),
            _Result(record={"eid": "4", "props": procedure["props"]}),
            _path(
                [failure, equipment, work_order, procedure],
                [
                    {"source": "1", "target": "2", "type": "OCCURRED_ON"},
                    {"source": "3", "target": "2", "type": "PERFORMED_ON"},
                    {
                        "source": "3",
                        "target": "4",
                        "type": "FOLLOWED_PROCEDURE",
                    },
                ],
            ),
            _Result(rows=[]),
        ]
    )

    result = fetch_graph(
        GraphRequest(
            graph_paths=[
                GraphNode(type="FailureEvent", id="FE-001"),
                GraphNode(type="Procedure", id="PROC-001"),
            ]
        ),
        session=session,
    )

    assert {node["id"] for node in result["nodes"]} == {
        "FailureEvent:FE-001",
        "Equipment:P-101",
        "WorkOrder:WO-1002",
        "Procedure:PROC-001",
    }
    assert {relationship["type"] for relationship in result["relationships"]} == {
        "OCCURRED_ON",
        "PERFORMED_ON",
        "FOLLOWED_PROCEDURE",
    }
    assert "shortestPath" in session.calls[2][0]


def test_single_citation_includes_bounded_evidence_neighborhood():
    chunk = {
        "eid": "10",
        "labels": ["Chunk"],
        "props": {
            "id": "DOC-LOG-001-C001",
            "text": "evidence",
            "embedding": [0.1],
        },
    }
    equipment = {
        "eid": "11",
        "labels": ["Equipment"],
        "props": {"tag_id": "P-101"},
    }
    session = _Session(
        [
            _Result(record={"eid": "10", "props": chunk["props"]}),
            _path(
                [chunk, equipment],
                [{"source": "10", "target": "11", "type": "MENTIONS"}],
            ),
        ]
    )

    result = fetch_graph(
        GraphRequest(
            graph_paths=[GraphNode(type="Chunk", id="DOC-LOG-001-C001")]
        ),
        session=session,
    )

    assert [relationship["type"] for relationship in result["relationships"]] == [
        "MENTIONS"
    ]
    chunk_result = next(node for node in result["nodes"] if node["type"] == "Chunk")
    assert "embedding" not in chunk_result["properties"]
    assert "*1..2" in session.calls[1][0]
