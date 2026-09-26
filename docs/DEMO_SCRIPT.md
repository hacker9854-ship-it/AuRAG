# AuRAG Five-Minute Demo

## Preflight

- API readiness is green.
- Frontend shows `Operational`.
- Use a Groq key with adequate 70B token headroom.
- Open `/investigate`, `/comparison`, `/predictive-watch`, and
  `/knowledge-risk` in separate tabs.
- Keep one existing Draft work order available for the decision step.

## 0:00–0:30 — Problem

“Plant knowledge is split across maintenance logs, procedures, people,
failures, and regulations. Search finds documents; it does not restore the
relationships needed to diagnose and act.”

Show the Command Center’s connected entity classes and four-step answer flow.

## 0:30–1:45 — Grounded investigation

Open Investigate and ask:

> What caused the P-101 failure?

Point out:

- specialist routing;
- concise operational answer;
- source citations;
- visible graph trail;
- evidence node and relationship counts;
- asynchronous RAGAS quality status.

## 1:45–2:35 — GraphRAG differentiation

Open Comparison and run:

> Why did P-101 fail in March 2025, and which maintenance action should
> prevent recurrence?

Show the answers independently. Call out GraphRAG-only sources and linked
relationship evidence rather than comparing only latency.

## 2:35–3:35 — Proactive action

Open Predictive Watch, select equipment, and increase drift.

Show:

- matched historical failure signature;
- proactive notification;
- generated work-order draft;
- editable description and recommended action.

Open the work order, save one edit, and accept or reject it. Point out the
persistent version and decision audit trail.

## 3:35–4:15 — Knowledge continuity

Open Knowledge Risk. Change the retirement horizon and show:

- ranked people at risk;
- equipment and failure knowledge attached to each person;
- uncovered assets;
- recommended capture/succession actions.

Mention that chat memory is user-scoped and recalled across browser sessions
through mem0, while graph evidence remains authoritative.

## 4:15–4:45 — Measured quality

Open Evaluation. Show:

- faithfulness, context precision, and answer relevancy;
- historical trend;
- agent/status filters;
- low-faithfulness review queue.

## 4:45–5:00 — Close

“AuRAG is not another chat wrapper. It turns fragmented operational records
into connected, cited, measurable, and actionable plant intelligence.”

End on the Command Center or the accepted work order.
