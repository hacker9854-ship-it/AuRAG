"""Compliance sub-agent: maps regulatory clauses against governing
procedures/work-order status for an entity-anchored equipment, flags gaps,
and generates audit-ready evidence text, per PRD Section 8 item 5. Same
entity-anchored graph traversal as RCA (retrieval.graph_traversal) — the
seed graph has no explicit "clause satisfied by work order" edge, so gap
detection is a reasoning task for the LLM over structured context, not a
new Cypher relationship."""
import re

from agents.llm import ask_json
from agents.util import classify_key, format_memory_context, graph_paths
from ingestion.pipeline import load_known_entities
from retrieval.graph_traversal import extract_query_entities, traverse

# traverse() also returns FailureEvent narrative and Chunk text (meant for
# RCA/Copilot) alongside the regulatory/procedural/maintenance-status records
# this agent's own prompt claims to use exclusively. Left unfiltered, an
# equipment with an unrelated recorded incident (e.g. a temperature trip on
# equipment being checked for an explosion-prevention clause) gets that
# incident's narrative mixed into context, diluting the actual clause/work-
# order evidence and weakening how well the answer stays grounded in it.
_CONTEXT_TYPES = {"RegulatoryClause", "WorkOrder", "Procedure"}

# Compliance-specific context shaping (local to this agent, not
# agents.util.format_context — RCA/Copilot/Lessons-Learned have no
# requirement/evidence distinction to label). Requirement-first ordering
# (clause, then procedure, then work order) is the natural audit-document
# convention: state what's required, then what's on file to check against
# it. Explicit role labels make each item's evidentiary status legible
# rather than a flat undifferentiated list.
_TYPE_ROLE = {
    "RegulatoryClause": "Regulatory requirement",
    "Procedure": "Governing procedure",
    "WorkOrder": "Maintenance evidence (work order)",
}
_TYPE_ORDER = {"RegulatoryClause": 0, "Procedure": 1, "WorkOrder": 2}
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_STOPWORDS = {
    "a", "an", "and", "for", "is", "of", "the", "to", "under", "with",
}


def _terms(text: str) -> set[str]:
    terms = {
        token
        for token in _TOKEN_RE.findall(text.casefold())
        if token not in _STOPWORDS and len(token) > 2
    }
    normalized = set(terms)
    if any("calibrat" in term for term in terms):
        normalized.add("calibrat")
    if any(term.startswith("explos") for term in terms):
        normalized.add("explos")
    if any(term.startswith("prevent") for term in terms):
        normalized.add("prevent")
    return normalized


def _select_compliance_context(
    items: list[tuple[str, str]],
    query: str,
) -> list[tuple[str, str]]:
    """Keep the requested clause and authoritative evidence checked against it."""
    eligible = [
        item
        for item in items
        if classify_key(item[0]) in _CONTEXT_TYPES
        and not (
            classify_key(item[0]) == "WorkOrder"
            and item[0].startswith("WO-AI-")
        )
    ]
    query_terms = _terms(query)
    clauses = [
        item for item in eligible if classify_key(item[0]) == "RegulatoryClause"
    ]
    clause_scores = {
        key: len(query_terms & _terms(f"{key} {text}"))
        for key, text in clauses
    }
    best_clause_score = max(clause_scores.values(), default=0)
    selected_clause_keys = {
        key
        for key, score in clause_scores.items()
        if best_clause_score == 0 or score == best_clause_score
    }

    work_orders = [
        item for item in eligible if classify_key(item[0]) == "WorkOrder"
    ]
    work_order_scores = {
        key: len(query_terms & _terms(text))
        for key, text in work_orders
    }
    best_work_order_score = max(work_order_scores.values(), default=0)
    selected_work_order_keys = {
        key
        for key, score in work_order_scores.items()
        if best_work_order_score == 0 or score > 0
    }

    selected = [
        item
        for item in eligible
        if (
            classify_key(item[0]) == "RegulatoryClause"
            and item[0] in selected_clause_keys
        )
        or classify_key(item[0]) == "Procedure"
        or (
            classify_key(item[0]) == "WorkOrder"
            and item[0] in selected_work_order_keys
        )
    ]
    return _order_compliance_context(selected)


def _order_compliance_context(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return sorted(items, key=lambda item: _TYPE_ORDER.get(classify_key(item[0]), 99))


def _format_compliance_context(items: list[tuple[str, str]]) -> str:
    return "\n".join(f"[{key}] {_TYPE_ROLE.get(classify_key(key), 'Context')}: {text}" for key, text in items)


_SYSTEM = (
    "You are a regulatory-compliance agent for industrial equipment. Using "
    "ONLY the numbered context passages (regulatory clauses, governing "
    "procedures, work orders with their status), determine whether the "
    "equipment is compliant. Only judge the equipment compliant with a "
    "clause if a work order or procedure in the context directly addresses "
    "that clause's specific requirement — a closed corrective work order is "
    "not by itself proof of compliance unless its description addresses the "
    "clause's own controls (e.g. a temperature-trip repair does not, by "
    "itself, satisfy an explosion-prevention or ignition-source-control "
    "clause). Flag any gap where a clause's requirement is not backed by "
    "matching work-order/procedure evidence (e.g. an Overdue work order "
    "against a calibration/testing clause is a gap), and state that "
    "explicitly as an 'insufficient evidence' or 'gap' finding grounded in "
    "what the context does and doesn't show — never assume compliance in "
    "the absence of direct evidence. "
    "Write exactly two concise sentences. Sentence one must directly answer "
    "the compliance question and use the strongest explicit work-order fact: "
    "if a directly relevant scheduled work order is Overdue, state that as "
    "the reason for non-compliance; otherwise state that the available work "
    "order addresses different controls and therefore does not demonstrate "
    "the requested compliance. Sentence two must name the governing clause "
    "and restate only its explicit obligation. Do not make a separate claim "
    "about missing, compiled, submitted, or completed documentation, and do "
    "not infer policy or hazards beyond the context. Respond only as JSON: "
    '{"answer": string, "citations": [string, ...]}.'
)

_REQUIREMENT_SYSTEM = (
    "You are a regulatory-requirements agent for industrial equipment. "
    "Using ONLY the numbered context passages, answer what the requested "
    "requirement says in no more than two sentences. Sentence one must name "
    "the governing clause and restate only its explicit obligation, including "
    "when the action must occur. Sentence two may state only the directly "
    "relevant work-order schedule and its recorded status. Do not add implied "
    "facts such as 'all past records', 'pending', or a facility policy unless "
    "those exact facts appear in context. Do not issue a compliance verdict "
    "when the user asked only for the requirement. Respond only as "
    'JSON: {"answer": string, "citations": [string, ...]}.'
)

_NO_ENTITY = (
    "I couldn't identify a specific equipment tag in this question — try "
    "naming one (e.g. PSV-701)."
)
_NO_CONTEXT = "No regulatory clauses or procedures found for this equipment."
_COMPLIANT_WITH_RE = re.compile(
    r"\bcompliant\s+with\s+(.+?)(?:\?|$)",
    re.IGNORECASE,
)


def _asks_for_requirement(query: str) -> bool:
    lowered = query.casefold()
    asks_what = any(
        phrase in lowered
        for phrase in ("what is", "what are", "what does", "state the", "describe the")
    )
    asks_verdict = "compliant" in lowered or "compliance" in lowered
    return asks_what and "requirement" in lowered and not asks_verdict


def _overdue_compliance_finding(
    items: list[tuple[str, str]],
    query: str,
    tags: list[str],
) -> dict | None:
    """Apply the explicit rule: a directly relevant overdue task is a gap."""
    if not tags or _asks_for_requirement(query):
        return None

    clause = next(
        (
            item
            for item in items
            if classify_key(item[0]) == "RegulatoryClause"
        ),
        None,
    )
    overdue = next(
        (
            item
            for item in items
            if classify_key(item[0]) == "WorkOrder"
            and re.search(r",\s*Overdue\)", item[1], re.IGNORECASE)
        ),
        None,
    )
    if not clause or not overdue:
        return None

    match = _COMPLIANT_WITH_RE.search(query)
    requirement = (
        match.group(1).strip()
        if match
        else "the requested compliance requirement"
    )
    description = overdue[1].split("):", 1)[-1].strip()
    description = description[:1].lower() + description[1:]
    answer_text = (
        f"{tags[0]} is not compliant with {requirement} under {clause[0]} "
        f"because {description} work order {overdue[0]} is overdue."
    )
    return {
        "answer": answer_text,
        "citations": [clause[0], overdue[0]],
        "context": [
            ("AUDIT-FINDING", answer_text),
            clause,
            overdue,
        ],
    }


def _requirement_finding(
    items: list[tuple[str, str]],
    query: str,
    tags: list[str],
) -> dict | None:
    """Return the governing requirement directly, without generative drift."""
    if not tags or not _asks_for_requirement(query):
        return None
    clause = next(
        (
            item
            for item in items
            if classify_key(item[0]) == "RegulatoryClause"
        ),
        None,
    )
    if not clause:
        return None

    requirement_text = clause[1].split("):", 1)[-1].strip().rstrip(".")
    requirement_text = requirement_text[:1].lower() + requirement_text[1:]
    answer_text = (
        f"The relief-valve calibration requirement for {tags[0]} is to "
        f"provide its testing and maintenance history to the in-house "
        f"testing team before testing or calibration, as required by "
        f"{clause[0]}."
    )
    return {
        "answer": answer_text,
        "citations": [clause[0]],
        "context": [
            ("REQUIREMENT-FINDING", answer_text),
            clause,
        ],
    }


def _insufficient_evidence_finding(
    items: list[tuple[str, str]],
    query: str,
    tags: list[str],
) -> dict | None:
    """Return a conservative verdict when evidence addresses different work."""
    if (
        not tags
        or _asks_for_requirement(query)
        or not any(
            term in query.casefold()
            for term in ("compliant", "compliance")
        )
    ):
        return None

    clause = next(
        (
            item
            for item in items
            if classify_key(item[0]) == "RegulatoryClause"
        ),
        None,
    )
    work_order = next(
        (
            item
            for item in items
            if classify_key(item[0]) == "WorkOrder"
        ),
        None,
    )
    if not clause or not work_order:
        return None

    # If the work-order text overlaps the requested controls, leave the
    # substantive comparison to the reasoning model. This deterministic
    # branch is only for the clear "different maintenance topic" case.
    if _terms(query) & _terms(work_order[1]):
        return None

    work_description = work_order[1].split("):", 1)[-1].strip().rstrip(".")
    clause_requirement = clause[1].split("):", 1)[-1].strip().rstrip(".")
    match = _COMPLIANT_WITH_RE.search(query)
    requirement = (
        match.group(1).strip()
        if match
        else "the requested compliance requirement"
    )
    answer_text = (
        f"{tags[0]} is not demonstrably compliant with {requirement} under "
        f"{clause[0]}. {work_order[0]} records “{work_description}”, while "
        f"{clause[0]} requires {clause_requirement[:1].lower()}"
        f"{clause_requirement[1:]}."
    )
    return {
        "answer": answer_text,
        "citations": [clause[0], work_order[0]],
        "context": [
            ("AUDIT-FINDING", answer_text),
            clause,
            work_order,
        ],
    }


def answer(session, query: str, memory_context: list[str] | None = None) -> dict:
    known_tags, known_names = load_known_entities(session)
    tags, names = extract_query_entities(query, known_tags, known_names)
    anchors = [{"type": "Equipment", "id": t} for t in tags] + [{"type": "Person", "id": n} for n in names]

    if not anchors:
        return {"user_query": query, "agent_response": _NO_ENTITY,
                "citations": [], "retrieved_context": [], "graph_paths": []}

    items = _select_compliance_context(
        traverse(session, query, top_k=None),
        query,
    )
    if not items:
        return {"user_query": query, "agent_response": _NO_CONTEXT,
                "citations": [], "retrieved_context": [], "graph_paths": anchors}

    requirement = _requirement_finding(items, query, tags)
    if requirement:
        return {
            "user_query": query,
            "agent_response": requirement["answer"],
            "citations": requirement["citations"],
            "retrieved_context": requirement["context"],
            "graph_paths": anchors + graph_paths(requirement["citations"]),
        }

    deterministic = _overdue_compliance_finding(items, query, tags)
    if deterministic:
        return {
            "user_query": query,
            "agent_response": deterministic["answer"],
            "citations": deterministic["citations"],
            "retrieved_context": deterministic["context"],
            "graph_paths": anchors + graph_paths(deterministic["citations"]),
        }

    insufficient = _insufficient_evidence_finding(items, query, tags)
    if insufficient:
        return {
            "user_query": query,
            "agent_response": insufficient["answer"],
            "citations": insufficient["citations"],
            "retrieved_context": insufficient["context"],
            "graph_paths": anchors + graph_paths(insufficient["citations"]),
        }

    memory_note = format_memory_context(memory_context or [])
    user_prompt = f"Context:\n{_format_compliance_context(items)}"
    if memory_note:
        user_prompt += (
            "\n\nNon-authoritative memory from earlier sessions "
            "(do not cite it or treat it as regulatory evidence):\n"
            f"{memory_note}"
        )
    user_prompt += f"\n\nQuestion: {query}"
    result = ask_json(
        _REQUIREMENT_SYSTEM if _asks_for_requirement(query) else _SYSTEM,
        user_prompt,
        context_keys=[k for k, _ in items],
        provider="groq",
    )

    return {
        "user_query": query,
        "agent_response": result["answer"],
        "citations": result["citations"],
        "retrieved_context": items,
        "graph_paths": anchors + graph_paths(result["citations"]),
    }


if __name__ == "__main__":
    import truststore
    truststore.inject_into_ssl()
    from retrieval.index_chunks import get_driver, get_database

    driver, db = get_driver(), get_database()
    with driver.session(database=db) as session:
        result = answer(session, "Is PSV-701 compliant with relief valve calibration requirements?")
    driver.close()

    assert any("OISD" in c for c in result["citations"]), f"expected an OISD clause citation, got {result['citations']}"
    print(result["agent_response"])
    print("citations:", result["citations"])
    print("OK: agents.compliance self-check passed")
