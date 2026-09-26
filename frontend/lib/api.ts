// Typed fetch wrappers matching backend/app/api/*.py's contracts exactly —
// no transform layer, the backend already returns UI-ready shapes.

import { getChatIdentity } from "@/lib/session";
import type { PredictiveNotification } from "@/lib/notifications";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function predictiveEventsUrl() {
  return `${API_URL}/api/events/predictive`;
}

export interface ReadinessResponse {
  status: "ready" | "degraded";
  ready: boolean;
  dependencies: Record<string, { status: "up" | "down"; detail?: string }>;
}

export async function getReadiness(): Promise<ReadinessResponse> {
  const res = await fetch(`${API_URL}/api/health/ready`, { cache: "no-store" });
  const body = await res.json().catch(() => null);
  if (body && typeof body.ready === "boolean") return body;
  throw new Error("Backend readiness is unavailable.");
}

export type RagasStatus = "scored" | "scoring" | "scoring_delayed" | "skipped_no_context" | "skipped_disabled" | "error";

export interface ChatResponse {
  user_query: string;
  intent: string;
  routing_confidence: number;
  routed_agent: string;
  agent_response: string;
  citations: string[];
  graph_paths: { type: string; id: string }[];
  score_id?: string | null;
  ragas_status: RagasStatus;
  ragas_scores: {
    faithfulness?: number;
    context_precision?: number;
    answer_relevancy?: number;
  };
  low_faithfulness: boolean;
  session_id?: string;
  memory_recalled?: number;
}

export interface RagasScoreResult {
  score_id: string;
  ragas_status: RagasStatus;
  ragas_scores: ChatResponse["ragas_scores"];
  low_faithfulness: boolean;
  detail?: string | null;
}

export class ChatError extends Error {
  constructor(detail: string) {
    super(detail);
    this.name = "ChatError";
  }
}

export async function postChat(query: string): Promise<ChatResponse> {
  const identity = getChatIdentity();
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, user_id: identity.userId, session_id: identity.sessionId }),
  });
  if (!res.ok) {
    // Backend's flat_http_exception_handler returns {"error": ..., "detail":
    // ...} directly as the top-level body (not nested under "detail").
    const body = await res.json().catch(() => ({}));
    throw new ChatError(body?.detail ?? "The chat service is temporarily unavailable.");
  }
  return res.json();
}

export async function getRagasScore(scoreId: string): Promise<RagasScoreResult> {
  const res = await fetch(`${API_URL}/api/chat/scores/${scoreId}`);
  if (!res.ok) throw new Error("RAGAS score fetch failed");
  return res.json();
}

export interface Equipment {
  tag_id: string;
  name: string;
  type: string;
}

export async function getEquipment(): Promise<Equipment[]> {
  const res = await fetch(`${API_URL}/api/equipment`);
  if (!res.ok) throw new Error("Failed to load equipment list");
  return res.json();
}

export interface TelemetryMatch {
  failure_event_id: string;
  similarity: number;
  symptom: string;
  root_cause: string;
}

export interface ReadingMeta {
  label: string;
  unit: string;
  nominal: number;
}

export interface ScanResponse {
  reading: Record<string, string | number>;
  reading_meta: Record<string, ReadingMeta>;
  matches: TelemetryMatch[];
  warning: {
    equipment: string;
    matched_failure_event: string;
    similarity: number;
    symptom: string;
    event_id?: string;
  } | null;
  predictive_event?: {
    id: string;
    status: string;
  } | null;
}

export async function scanTelemetry(
  equipmentTag: string,
  driftToward: string | null,
  driftPct: number
): Promise<ScanResponse> {
  const res = await fetch(`${API_URL}/api/telemetry/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ equipment_tag: equipmentTag, drift_toward: driftToward, drift_pct: driftPct }),
  });
  if (!res.ok) throw new Error("Telemetry scan failed");
  return res.json();
}

export interface WorkOrderRecord {
  id: string;
  date: string;
  type: string;
  status: string;
  equipment: string;
  description: string;
  recommended_action: string;
  source?: string;
  version: number;
  predictive_event_id?: string | null;
  created_at?: string;
  updated_at?: string;
  decisions?: Array<Record<string, unknown>>;
}

export async function draftWorkOrder(
  equipmentTag: string,
  topMatch: TelemetryMatch,
  eventId?: string | null,
): Promise<WorkOrderRecord> {
  const identity = getChatIdentity();
  const res = await fetch(`${API_URL}/api/telemetry/draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      equipment_tag: equipmentTag,
      top_match: topMatch,
      event_id: eventId,
      actor: identity.userId,
    }),
  });
  if (!res.ok) throw new Error("Draft generation failed");
  return res.json();
}

export async function getWorkOrders(status?: string): Promise<WorkOrderRecord[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const res = await fetch(`${API_URL}/api/work-orders${query}`);
  if (!res.ok) throw new Error("Failed to load work orders.");
  const body = await res.json();
  return body.items;
}

export async function getWorkOrder(workOrderId: string): Promise<WorkOrderRecord> {
  const res = await fetch(`${API_URL}/api/work-orders/${encodeURIComponent(workOrderId)}`);
  if (!res.ok) throw new Error("Failed to load work order.");
  return res.json();
}

export async function updateWorkOrder(
  workOrderId: string,
  patch: {
    expected_version: number;
    description: string;
    recommended_action: string;
  },
): Promise<WorkOrderRecord> {
  const identity = getChatIdentity();
  const res = await fetch(`${API_URL}/api/work-orders/${encodeURIComponent(workOrderId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...patch, actor: identity.userId }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? "Work-order update failed.");
  }
  return res.json();
}

export async function decideWorkOrder(
  workOrderId: string,
  decision: {
    decision: "accept" | "reject";
    expected_version: number;
    reason?: string | null;
  },
): Promise<WorkOrderRecord> {
  const identity = getChatIdentity();
  const res = await fetch(`${API_URL}/api/work-orders/${encodeURIComponent(workOrderId)}/decisions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...decision, actor: identity.userId }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? "Work-order decision failed.");
  }
  return res.json();
}

export async function getNotifications(): Promise<PredictiveNotification[]> {
  const res = await fetch(`${API_URL}/api/notifications`);
  if (!res.ok) throw new Error("Failed to load predictive notifications.");
  const body = await res.json();
  return body.items;
}

export async function markNotificationRead(eventId: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/notifications/${encodeURIComponent(eventId)}/read`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to update notification.");
}

export interface GraphNode {
  id: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphRelationship {
  source: string;
  target: string;
  type: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  relationships: GraphRelationship[];
}

export async function fetchGraph(graphPaths: { type: string; id: string }[]): Promise<GraphResponse> {
  const res = await fetch(`${API_URL}/api/graph`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ graph_paths: graphPaths }),
  });
  if (!res.ok) throw new Error("Graph fetch failed");
  return res.json();
}

export interface KnowledgeRiskAction {
  type: string;
  priority: string;
  description: string;
  equipment?: string[];
}

export interface PersonKnowledgeRisk {
  person_id: string;
  name: string;
  role: string | null;
  department: string | null;
  years_to_retirement: number;
  risk_score: number;
  severity: "critical" | "elevated" | "monitored";
  work_orders: string[];
  equipment: string[];
  critical_equipment: string[];
  failure_events: string[];
  documents: string[];
  uncovered_equipment: string[];
  knowledge_coverage: {
    covered_assets: number;
    uncovered_assets: number;
    coverage_pct: number;
  };
  recommended_actions: KnowledgeRiskAction[];
}

export interface KnowledgeRiskResponse {
  retirement_horizon: number;
  summary: {
    people_at_risk: number;
    critical: number;
    elevated: number;
    uncovered_assets: number;
  };
  people: PersonKnowledgeRisk[];
}

export async function getKnowledgeRisk(retirementHorizon = 5): Promise<KnowledgeRiskResponse> {
  const res = await fetch(`${API_URL}/api/knowledge-risk?retirement_horizon=${retirementHorizon}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? "Failed to load knowledge-retirement risk.");
  }
  return res.json();
}

export interface ComparisonAnswer {
  user_query: string;
  agent_response: string;
  citations: string[];
  retrieved_context: [string, string][];
  graph_paths: { type: string; id: string }[];
  latency_ms: number;
  source_count: number;
}

export interface ComparisonResponse {
  query: string;
  graph_rag: ComparisonAnswer;
  plain_rag: ComparisonAnswer;
  comparison_metrics: {
    shared_sources: string[];
    graph_only_sources: string[];
    plain_only_sources: string[];
    source_overlap_pct: number;
    graph_relationship_evidence: number;
  };
}

export async function postComparison(query: string): Promise<ComparisonResponse> {
  const res = await fetch(`${API_URL}/api/comparison`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? "Comparison failed.");
  }
  return res.json();
}

export interface EvaluationRecord {
  score_id: string;
  query: string;
  answer: string;
  routed_agent: string;
  citations: string[];
  graph_paths: { type: string; id: string }[];
  retrieved_context: [string, string][];
  ragas_status: RagasStatus;
  ragas_scores: ChatResponse["ragas_scores"];
  low_faithfulness: boolean;
  created_at: string;
  completed_at: string | null;
  scoring_duration_ms: number | null;
  detail: string | null;
}

export interface EvaluationSummary {
  total: number;
  status_counts: Record<string, number>;
  agent_counts: Record<string, number>;
  low_faithfulness_count: number;
  averages: {
    faithfulness: number | null;
    context_precision: number | null;
    answer_relevancy: number | null;
  };
  trend: Array<{
    day: string;
    total: number;
    faithfulness: number | null;
    context_precision: number | null;
    answer_relevancy: number | null;
    low_faithfulness_count: number;
  }>;
}

export interface EvaluationQuery {
  limit?: number;
  offset?: number;
  status?: string;
  agent?: string;
  low_faithfulness?: boolean;
}

export interface EvaluationPage {
  items: EvaluationRecord[];
  limit: number;
  offset: number;
  total: number;
  has_more: boolean;
}

export async function getEvaluationResults(query: EvaluationQuery = {}): Promise<EvaluationPage> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit ?? 20));
  params.set("offset", String(query.offset ?? 0));
  if (query.status) params.set("status", query.status);
  if (query.agent) params.set("agent", query.agent);
  if (query.low_faithfulness !== undefined) {
    params.set("low_faithfulness", String(query.low_faithfulness));
  }
  const res = await fetch(`${API_URL}/api/evaluations?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to load evaluation history.");
  return res.json();
}

export async function getEvaluationSummary(): Promise<EvaluationSummary> {
  const res = await fetch(`${API_URL}/api/evaluations/summary`);
  if (!res.ok) throw new Error("Failed to load evaluation summary.");
  return res.json();
}

// Enterprise Automations & Governance
export interface AutomationPolicy {
  policy_id: string;
  site_id: string;
  name: string;
  description?: string | null;
  trigger_type: string;
  action_type: string;
  target_system: string;
  approval_threshold: "REQUIRES_APPROVAL" | "AUTONOMOUS";
  parameters: Record<string, unknown>;
  rollback_guidance?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ApprovalRecord {
  approval_id: string;
  action_type: string;
  target_system: string;
  payload: Record<string, unknown>;
  requested_by: string;
  site_id: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "AUTONOMOUS_EXECUTED";
  reviewed_by?: string | null;
  rollback_guidance?: string | null;
  created_at?: string;
  reviewed_at?: string | null;
}

export interface EvaluationRemediation {
  remediation_id: string;
  score_id: string;
  user_id: string;
  site_id: string;
  reason: string;
  incorrect_snippets: string[];
  correction_notes: string;
  status: "PENDING_REINDEX" | "REINDEXED" | "RESOLVED";
  created_at?: string;
  resolved_at?: string | null;
  resolved_by?: string | null;
}

export async function getAutomationPolicies(): Promise<{ policies: AutomationPolicy[]; total: number }> {
  const res = await fetch(`${API_URL}/api/automations/policies`);
  if (!res.ok) throw new Error("Failed to load automation policies.");
  return res.json();
}

export async function evaluateAutomation(payload: {
  trigger_type: string;
  context_data: Record<string, unknown>;
  dry_run?: boolean;
}): Promise<any> {
  const res = await fetch(`${API_URL}/api/automations/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to evaluate automation.");
  return res.json();
}

export async function getApprovalQueue(status?: string): Promise<{ queue: ApprovalRecord[]; total: number }> {
  const url = status
    ? `${API_URL}/api/automations/queue?status=${status}`
    : `${API_URL}/api/automations/queue`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to load approval queue.");
  return res.json();
}

export async function reviewApproval(
  approvalId: string,
  action: "APPROVED" | "REJECTED",
  notes: string = ""
): Promise<any> {
  const res = await fetch(`${API_URL}/api/automations/queue/${approvalId}/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, notes }),
  });
  if (!res.ok) throw new Error("Failed to submit approval review.");
  return res.json();
}

export async function getRemediations(status?: string): Promise<{ remediations: EvaluationRemediation[]; total: number }> {
  const url = status
    ? `${API_URL}/api/automations/remediations?status=${status}`
    : `${API_URL}/api/automations/remediations`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to load remediations.");
  return res.json();
}

export async function submitRemediation(payload: {
  score_id: string;
  reason: string;
  incorrect_snippets?: string[];
  correction_notes: string;
}): Promise<any> {
  const res = await fetch(`${API_URL}/api/automations/remediations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit evaluation remediation.");
  return res.json();
}

export async function updateRemediationStatus(
  remediationId: string,
  status: "PENDING_REINDEX" | "REINDEXED" | "RESOLVED"
): Promise<any> {
  const res = await fetch(`${API_URL}/api/automations/remediations/${remediationId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error("Failed to update remediation status.");
  return res.json();
}

