// Industrial Knowledge Intelligence — Neo4j schema (Phase 1 constraints,
// Phase 3 vector index)
//
// Node key strategy: use PRD-specified keys where given; generated ids
// (document_id / chunk_id / person_id) for the three node types the PRD
// left without one (Document, Chunk, Person) — see NOTES.md "Node unique
// keys" for reasoning.

CREATE CONSTRAINT equipment_tag_id IF NOT EXISTS
FOR (e:Equipment) REQUIRE e.tag_id IS UNIQUE;

CREATE CONSTRAINT document_id IF NOT EXISTS
FOR (d:Document) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT chunk_id IF NOT EXISTS
FOR (c:Chunk) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT person_id IF NOT EXISTS
FOR (p:Person) REQUIRE p.person_id IS UNIQUE;

CREATE CONSTRAINT workorder_id IF NOT EXISTS
FOR (w:WorkOrder) REQUIRE w.id IS UNIQUE;

CREATE CONSTRAINT failureevent_id IF NOT EXISTS
FOR (f:FailureEvent) REQUIRE f.id IS UNIQUE;

CREATE CONSTRAINT clause_id IF NOT EXISTS
FOR (r:RegulatoryClause) REQUIRE r.clause_id IS UNIQUE;

CREATE CONSTRAINT procedure_id IF NOT EXISTS
FOR (p:Procedure) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT evaluation_score_id IF NOT EXISTS
FOR (e:EvaluationRun) REQUIRE e.score_id IS UNIQUE;

CREATE CONSTRAINT predictive_event_id IF NOT EXISTS
FOR (e:PredictiveEvent) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT predictive_event_dedupe_key IF NOT EXISTS
FOR (e:PredictiveEvent) REQUIRE e.dedupe_key IS UNIQUE;

CREATE CONSTRAINT notification_id IF NOT EXISTS
FOR (n:Notification) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT work_order_decision_id IF NOT EXISTS
FOR (d:WorkOrderDecision) REQUIRE d.id IS UNIQUE;

// Lookup indexes for common non-unique query patterns (Phase 1: cheap to
// add now, useful once RCA/Compliance agents start traversing).
CREATE INDEX equipment_type IF NOT EXISTS FOR (e:Equipment) ON (e.type);
CREATE INDEX failureevent_date IF NOT EXISTS FOR (f:FailureEvent) ON (f.date);
CREATE INDEX workorder_date IF NOT EXISTS FOR (w:WorkOrder) ON (w.date);
CREATE INDEX person_years_to_retirement IF NOT EXISTS FOR (p:Person) ON (p.years_to_retirement);
CREATE INDEX evaluation_created_at IF NOT EXISTS FOR (e:EvaluationRun) ON (e.created_at);
CREATE INDEX evaluation_status IF NOT EXISTS FOR (e:EvaluationRun) ON (e.ragas_status);
CREATE INDEX predictive_event_detected_at IF NOT EXISTS FOR (e:PredictiveEvent) ON (e.detected_at);
CREATE INDEX predictive_event_status IF NOT EXISTS FOR (e:PredictiveEvent) ON (e.status);
CREATE INDEX work_order_status IF NOT EXISTS FOR (w:WorkOrder) ON (w.status);

// Phase 3: native vector index over Chunk embeddings. sentence-transformers
// all-MiniLM-L6-v2 -> 384 dims, cosine similarity (standard for that model).
CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 384,
  `vector.similarity_function`: 'cosine'
}};
