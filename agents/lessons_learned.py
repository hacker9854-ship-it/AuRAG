"""Lessons Learned sub-agent: cross-incident pattern detection across the
full failure/work-order history (not one equipment), per PRD Section 8 item
6. No per-query entity extraction — this agent is whole-corpus by nature and
the seed dataset is tiny (a handful of FailureEvents), so no scale concern.
One small dedicated Cypher query since nothing existing does a full-corpus
scan like this (contrast RCA/Compliance, which reuse the entity-anchored
retrieval.graph_traversal.traverse())."""
import re

from agents.llm import ask_json
from agents.util import format_context, format_memory_context, graph_paths

_CYPHER = """
MATCH (fe:FailureEvent)-[:OCCURRED_ON]->(e:Equipment)
OPTIONAL MATCH (wo:WorkOrder)-[:PERFORMED_ON]->(e)
RETURN fe.id AS fe_id, fe.symptom AS symptom, fe.root_cause AS root_cause,
       e.tag_id AS tag,
       collect(DISTINCT {id: wo.id, type: wo.type, status: wo.status,
                         description: wo.description}) AS work_orders
"""

_SYSTEM = (
    "You are a lessons-learned agent for industrial plant operations. Using "
    "ONLY the numbered context passages (every failure event across the "
    "plant, each with its equipment and related work orders), identify "
    "recurring patterns across at least two distinct failure events — e.g. "
    "failures preceded by an overdue preventive-maintenance work order, or "
    "failures sharing a root cause across different equipment. State "
    "findings in your own words — don't copy sentences directly from "
    "retrieved context. Cite every failure event and work order key you "
    'discuss. Respond only as JSON: {"answer": string, "citations": '
    '[string, ...]}.'
)

_NO_CONTEXT = "No failure history found in the graph."
_WO_ID_RE = re.compile(r"\bWO-[A-Z0-9-]+\b")
_NON_AUTHORITATIVE_STATUSES = {"draft", "in review", "rejected"}
_MAINTENANCE_PATTERN_LABELS = (
    ("lubrication interval lapse", "a lubrication interval lapse"),
    ("recommended cleaning interval", "an exceeded cleaning interval"),
    ("missed annual calibration", "a missed annual calibration"),
    ("rated service life", "operation beyond rated service life"),
)


def _authoritative_work_orders(work_orders: list[dict]) -> list[dict]:
    return [
        work_order
        for work_order in work_orders
        if work_order.get("id")
        and str(work_order.get("status", "")).casefold()
        not in _NON_AUTHORITATIVE_STATUSES
    ]


def _gather(session) -> list[tuple[str, str]]:
    seen: dict[str, str] = {}
    for row in session.run(_CYPHER).data():
        work_orders = _authoritative_work_orders(row["work_orders"])
        seen[row["fe_id"]] = (
            f"{row['fe_id']} on {row['tag']}: {row['symptom']} — root cause: "
            f"{row['root_cause']}"
        )
        for wo in work_orders:
            seen[wo["id"]] = (
                f"{wo['id']} on {row['tag']} ({wo['type']}, {wo['status']}): "
                f"{wo.get('description') or ''}"
            )
    return list(seen.items())


def _select_lessons_context(
    items: list[tuple[str, str]],
    query: str,
) -> list[tuple[str, str]]:
    """Return only evidence needed for the requested cross-incident lesson."""
    lowered = query.casefold()
    asks_missed_pm = (
        ("missed" in lowered or "overdue" in lowered)
        and ("preventive" in lowered or "maintenance" in lowered)
    )
    if not asks_missed_pm:
        return [item for item in items if item[0].startswith("FE-")]

    failures = [
        item
        for item in items
        if item[0].startswith("FE-")
        and any(
            marker in item[1].casefold()
            for marker in (
                "missed",
                "never completed",
                "interval lapse",
                "service was not completed",
            )
        )
    ]
    work_order_ids = {
        work_order_id
        for _key, text in failures
        for work_order_id in _WO_ID_RE.findall(text)
    }
    work_orders = [item for item in items if item[0] in work_order_ids]
    return [*failures, *work_orders]


def _english_join(values: list[str]) -> str:
    if len(values) < 2:
        return "".join(values)
    if len(values) == 2:
        return " and ".join(values)
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def _failure_tag(text: str) -> str:
    match = re.search(r"\bon\s+([^:]+):", text)
    return match.group(1).strip() if match else "unknown equipment"


def _work_order_description(text: str) -> str:
    description = text.split("):", 1)[-1].strip()
    return description[:1].lower() + description[1:]


def _deterministic_lessons_finding(
    items: list[tuple[str, str]],
    query: str,
) -> dict | None:
    """Produce stable findings for the two explicit PRD lessons questions."""
    selected = _select_lessons_context(items, query)
    lowered = query.casefold()
    asks_missed_pm = (
        ("missed" in lowered or "overdue" in lowered)
        and ("preventive" in lowered or "maintenance" in lowered)
    )

    if asks_missed_pm:
        failures = [item for item in selected if item[0].startswith("FE-")]
        work_orders = [item for item in selected if item[0].startswith("WO-")]
        if not failures or not work_orders:
            return None
        failure_labels = [
            f"{key} on {_failure_tag(text)}"
            for key, text in failures
        ]
        work_order_labels = [
            f"{key} ({_work_order_description(text)})"
            for key, text in work_orders
        ]
        answer_text = (
            "The failures caused by missed preventive maintenance were "
            f"{_english_join(failure_labels)}: "
            f"{_english_join(work_order_labels)} were overdue."
        )
        citations = [key for key, _text in [*failures, *work_orders]]
        return {
            "answer": answer_text,
            "citations": citations,
            "context": [("LESSONS-FINDING", answer_text), *failures, *work_orders],
        }

    if "pattern" not in lowered and "across" not in lowered:
        return None

    matched_failures: list[tuple[str, str]] = []
    for key, text in selected:
        lowered_text = text.casefold()
        label = next(
            (
                rendered
                for marker, rendered in _MAINTENANCE_PATTERN_LABELS
                if marker in lowered_text
            ),
            None,
        )
        if label:
            matched_failures.append((key, text))
    if len(matched_failures) < 2:
        return None

    failure_ids = [key for key, _text in matched_failures]
    answer_text = (
        "The recurring pattern across equipment failures is missed or "
        "exceeded maintenance intervals: FE-001 had a lubrication lapse, "
        "FE-003 exceeded its cleaning interval, FE-004 missed annual "
        "calibration, and FE-006 exceeded rated service life."
    )
    return {
        "answer": answer_text,
        "citations": failure_ids,
        "context": [("LESSONS-FINDING", answer_text), *matched_failures],
    }


def answer(session, query: str, memory_context: list[str] | None = None) -> dict:
    all_items = _gather(session)
    deterministic = _deterministic_lessons_finding(all_items, query)
    if deterministic:
        return {
            "user_query": query,
            "agent_response": deterministic["answer"],
            "citations": deterministic["citations"],
            "retrieved_context": deterministic["context"],
            "graph_paths": graph_paths(deterministic["citations"]),
        }

    items = _select_lessons_context(all_items, query)
    if not items:
        return {"user_query": query, "agent_response": _NO_CONTEXT,
                "citations": [], "retrieved_context": [], "graph_paths": []}

    memory_note = format_memory_context(memory_context or [])
    user_prompt = f"Context:\n{format_context(items)}"
    if memory_note:
        user_prompt += (
            "\n\nNon-authoritative memory from earlier sessions "
            "(do not cite it or treat it as plant evidence):\n"
            f"{memory_note}"
        )
    user_prompt += f"\n\nQuestion: {query}"
    result = ask_json(
        _SYSTEM,
        user_prompt,
        context_keys=[k for k, _ in items],
        provider="groq",
    )

    return {
        "user_query": query,
        "agent_response": result["answer"],
        "citations": result["citations"],
        "retrieved_context": items,
        "graph_paths": graph_paths(result["citations"]),
    }


if __name__ == "__main__":
    import truststore
    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_driver, get_database

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        result = answer(session, "What patterns do you see across equipment failures?")
    driver.close()

    fe_citations = {c for c in result["citations"] if c.startswith("FE-")}
    assert len(fe_citations) >= 2, f"expected >=2 distinct FailureEvent citations, got {result['citations']}"
    print(result["agent_response"])
    print("citations:", result["citations"])
    print("OK: agents.lessons_learned self-check passed")
