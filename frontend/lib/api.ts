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
  return Array.isArray(body?.items) ? body.items : Array.isArray(body) ? body : [];
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
  graph_status?: "ONLINE" | "DEGRADED / FALLBACK" | string;
  fallback_active?: boolean;
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

export interface GraphHealthResponse {
  status: "ONLINE" | "DEGRADED" | string;
  state_label: "ONLINE" | "DEGRADED / FALLBACK" | string;
  connected: boolean;
  mode: string;
  database?: string;
  uri?: string;
  detail?: string;
  fallback_active: boolean;
}

export async function fetchGraphHealth(): Promise<GraphHealthResponse> {
  const res = await fetch(`${API_URL}/api/graph/health`, { cache: "no-store" });
  if (!res.ok) {
    return {
      status: "DEGRADED",
      state_label: "DEGRADED / FALLBACK",
      connected: false,
      mode: "FALLBACK_REPRESENTATION",
      fallback_active: true,
    };
  }
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
  const data = await res.json();
  if (data && data.error) {
    throw new Error(data.detail || data.error);
  }
  return data;
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

// ---------------------------------------------------------------------------
// Bitshala BOSS Battle: Machine Money Micro-Settlement Layer (Sections 11-20)
// ---------------------------------------------------------------------------

export interface MachineMoneyHealth {
  provider_name: string;
  provider_mode?: "MOCK" | "LIVE";
  settlement_source?: "SIMULATED" | "LIGHTNING_NODE";
  is_live?: boolean;
  is_connected: boolean;
  network: string;
  is_mock?: boolean;
  balance_sats?: number;
  node_pubkey?: string;
  latency_ms?: number;
  details: Record<string, any>;
}

export interface ServiceDefinition {
  service_id: string;
  name: string;
  provider_id: string;
  provider_name: string;
  price_sats: number;
  equipment_class: string;
  description: string;
  estimated_duration_hours: number;
  parts_included: string[];
  is_mock: boolean;
}

export interface ProviderRegistryResponse {
  registry_title: string;
  disclosure: string;
  total_services: number;
  total_providers: number;
  providers: Array<{
    provider_id: string;
    provider_name: string;
    supported_services: string[];
    network: string;
    status: string;
  }>;
  services: ServiceDefinition[];
}

export interface M2MTriggerResult {
  status: string;
  payment_id: string;
  idempotency_key: string;
  amount_sats: number;
  service?: {
    id: string;
    name: string;
    provider: string;
  };
  evidence_package: {
    reason: string;
    confidence: number;
    evidence: string[];
    equipment: string;
    matched_failure_event?: string;
    related_work_order?: string;
    governing_procedure?: string;
    cross_layer_justification?: string;
  };
  approval_id?: string | null;
  payment_hash?: string;
  preimage?: string;
  bolt11?: string;
  payment_record?: any;
  paid_at?: string;
  is_duplicate_prevented: boolean;
}

export interface PaymentTrailResponse {
  payment_id: string;
  found: boolean;
  status?: string;
  amount_sats?: number;
  payment_hash?: string;
  preimage?: string;
  service_provider?: string;
  work_order?: { id?: string; description?: string };
  predictive_trigger?: { event_id?: string; event_type?: string; confidence?: number };
  failure_signature?: { failure_id?: string; title?: string };
  equipment?: { tag_id?: string; name?: string };
  graph_story?: string[];
  explanation?: string;
}

export async function getMachineMoneyHealth(): Promise<MachineMoneyHealth> {
  const res = await fetch(`${API_URL}/api/machine-money/health`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch Machine Money health.");
  return res.json();
}

export async function getMachineMoneyProviders(): Promise<ProviderRegistryResponse> {
  const res = await fetch(`${API_URL}/api/machine-money/providers`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch Machine Money provider registry.");
  return res.json();
}

export async function triggerMachineMoneyFromTelemetry(payload: {
  equipment_tag: string;
  event_id?: string;
  failure_event_id?: string;
  confidence?: number;
  work_order_id?: string;
  bypass_policy?: boolean;
}): Promise<M2MTriggerResult> {
  const res = await fetch(`${API_URL}/api/machine-money/trigger-from-telemetry`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Telemetry trigger failed" }));
    throw new Error(err.detail || "Failed to trigger Machine Money settlement");
  }
  return res.json();
}

export async function simulateMachineMoney(payload: {
  site_id?: string;
  equipment_id: string;
  service_id?: string;
  predictive_event_id?: string;
  amount_sats?: number;
  confidence?: number;
}): Promise<any> {
  const res = await fetch(`${API_URL}/api/machine-money/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to run Machine Money simulation.");
  return res.json();
}

export async function approveMachineMoneyPayment(
  paymentId: string,
  reviewerId: string = "lead-operator-mumbai",
  reviewNotes: string = "Operator approved high-value maintenance dispatch."
): Promise<any> {
  const res = await fetch(`${API_URL}/api/machine-money/payments/${paymentId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviewer_id: reviewerId, review_notes: reviewNotes }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Approval failed" }));
    throw new Error(err.detail || "Failed to approve payment");
  }
  return res.json();
}

export async function getPaymentGraphTrail(paymentId: string): Promise<PaymentTrailResponse> {
  const res = await fetch(`${API_URL}/api/machine-money/payments/${paymentId}/trail`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch payment graph trail.");
  return res.json();
}

export async function listMachineMoneyPayments(limit: number = 20): Promise<any[]> {
  const res = await fetch(`${API_URL}/api/machine-money/payments?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to list Machine Money payments.");
  return res.json();
}

export async function getPaymentEvidence(paymentId: string): Promise<any> {
  const res = await fetch(`${API_URL}/api/machine-money/evidence/${paymentId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch payment evidence package.");
  return res.json();
}

// ---------------------------------------------------------------------------
// Judge Mode Orchestration Types & Client Endpoints (Phase 2)
// ---------------------------------------------------------------------------

export type ExecutionStage =
  | "ANOMALY_DETECTED"
  | "EVIDENCE_MATCHED"
  | "QUOTE_RESOLVED"
  | "POLICY_EVALUATED"
  | "INVOICE_GENERATED"
  | "PAYMENT_AUTHORIZED"
  | "SETTLEMENT_CONFIRMED"
  | "GRAPH_LINKED"
  | "OUTCOME_RESOLVED";

export interface ExecutionStageEvent {
  stage: ExecutionStage;
  status: "SUCCESS" | "PENDING_APPROVAL" | "FAILED" | "RUNNING";
  elapsed_ms: number;
  message: string;
  evidence_refs: string[];
  data: Record<string, any>;
  timestamp: string;
}

export interface JudgeExecutionRequest {
  scenario?: "INDUSTRIAL_EMERGENCY" | "POLICY_ESCALATION" | "PROVIDER_FAILURE" | "PUBLIC_DATASET_REPLAY";
  equipment_id?: string;
  override_cost_sats?: number;
  auto_approve?: boolean;
}

export interface JudgeExecutionResponse {
  execution_id: string;
  scenario: string;
  status: "SUCCESS" | "PENDING_APPROVAL" | "FAILED";
  total_elapsed_ms: number;
  events: ExecutionStageEvent[];
  payment_record?: {
    payment_id?: string;
    amount_sats?: number;
    status?: string;
    payment_hash?: string;
    preimage?: string;
    bolt11?: string;
    work_order_id?: string;
    event_id?: string;
    vendor_name?: string;
    paid_at?: string;
    retry_guidance?: string;
    idempotency_key?: string;
    error_code?: string;
    error_message?: string;
    [key: string]: any;
  } | null;
  evidence_package?: Record<string, any> | null;
  provider_mode: string;
  summary: string;
}

export async function executeJudgeMode(
  payload: JudgeExecutionRequest = { scenario: "INDUSTRIAL_EMERGENCY", equipment_id: "P-101A" }
): Promise<JudgeExecutionResponse> {
  const res = await fetch(`${API_URL}/api/machine-money/judge/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Judge Mode execution failed." }));
    throw new Error(err.detail || "Judge Mode execution failed.");
  }
  return res.json();
}

export async function resetJudgeMode(): Promise<{ status: string; message: string; ready: boolean }> {
  const res = await fetch(`${API_URL}/api/machine-money/judge/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to reset Judge Mode scenario.");
  return res.json();
}

export interface ProofPackageResponse {
  identity: {
    payment_id: string;
    idempotency_key: string;
    created_at: string;
    settled_at?: string | null;
  };
  payment: {
    amount_sats: number;
    amount_msat: number;
    fee_sats: number;
    status: string;
    provider: string;
    network: string;
    bolt11: string;
    memo: string;
  };
  policy: {
    policy_id: string;
    policy_name: string;
    decision: string;
    cap_sats: number;
    confidence_score: number;
    evaluated_by: string;
  };
  operational_context: {
    equipment_id: string;
    event_id: string;
    work_order_id: string;
    failure_event_id: string;
    vendor_id?: string;
    vendor_name: string;
    vendor_pubkey?: string;
    reason: string;
    governing_procedure: string;
  };
  cryptographic_proof: {
    payment_hash: string;
    preimage: string;
    formula: string;
    is_verified: boolean;
    verification_mode: string;
    status_label: string;
  };
  graph_links: {
    equipment_tag: string;
    predictive_event: string;
    work_order: string;
    payment_node: string;
    lineage: string[];
    trail?: any;
  };
  audit: {
    audit_ledger_status: string;
    table: string;
    integrity: string;
    recorded_at: string;
  };
  provider_mode: string;
}

export interface JudgeScenarioFixture {
  scenario_id: string;
  site_id: string;
  equipment_id: string;
  equipment_name: string;
  sensor_id: string;
  reading: number;
  threshold: number;
  unit: string;
  iso_zone: string;
  failure_signature: string;
  failure_title: string;
  procedure_id: string;
  procedure_title: string;
  work_order_id: string;
  service_type: string;
  canonical_payment_sats: number;
  spending_cap_sats: number;
  provider_mode: string;
  settlement_source: string;
  selected_vendor: string;
  selected_vendor_id: string;
  selected_vendor_pubkey: string;
  selection_strategy: string;
  candidates_count: number;
}

export async function getJudgeScenarioFixture(): Promise<JudgeScenarioFixture> {
  const res = await fetch(`${API_URL}/api/machine-money/judge/fixture`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch judge scenario fixture.");
  return res.json();
}

export async function getPaymentProofPackage(paymentId: string): Promise<ProofPackageResponse> {
  const res = await fetch(`${API_URL}/api/machine-money/payments/${paymentId}/proof-package`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch payment proof package.");
  return res.json();
}

export type SelectionStrategy = "FASTEST_SLA" | "LOWEST_COST" | "HIGHEST_RELIABILITY" | "BALANCED";

export interface VendorQuoteCandidate {
  candidate_id: string;
  vendor_id: string;
  vendor_name: string;
  node_pubkey: string;
  service_id: string;
  service_name: string;
  amount_sats: number;
  sla_hours: number;
  reliability_score: number;
  reputation_tier: string;
  parts_included: string[];
  is_synthetic: boolean;
  within_policy_cap: boolean;
  score: number;
  valid_until: string;
  bolt11?: string;
  payment_hash?: string;
  vendor_node_type?: string;
}

export interface VendorRFQRequest {
  equipment_id?: string;
  service_id?: string;
  strategy?: SelectionStrategy;
  max_budget_sats?: number;
}

export interface VendorRFQResponse {
  rfq_id: string;
  requested_at: string;
  service_id: string;
  equipment_id: string;
  strategy: SelectionStrategy;
  policy_cap_sats: number;
  candidates: VendorQuoteCandidate[];
  selected_vendor: VendorQuoteCandidate;
  selection_rationale: string;
  scoring_model: Record<string, any>;
  is_synthetic: boolean;
  synthetic_disclosure: string;
}

export async function requestVendorRFQ(req?: VendorRFQRequest): Promise<VendorRFQResponse> {
  const res = await fetch(`${API_URL}/api/machine-money/rfq`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req || {}),
  });
  if (!res.ok) throw new Error("Failed to request vendor RFQ.");
  return res.json();
}

export async function getServiceRFQ(
  serviceId: string,
  strategy: SelectionStrategy = "FASTEST_SLA",
  maxBudgetSats: number = 500,
  equipmentId: string = "P-101A"
): Promise<VendorRFQResponse> {
  const params = new URLSearchParams({
    strategy,
    max_budget_sats: maxBudgetSats.toString(),
    equipment_id: equipmentId,
  });
  const res = await fetch(`${API_URL}/api/machine-money/rfq/${serviceId}?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to load RFQ for service ${serviceId}.`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Phase 5: Machine Money Intelligence & Industrial Economics Contracts
// ---------------------------------------------------------------------------

export interface VendorSpendItem {
  vendor_name: string;
  spend_sats: number;
  payment_count: number;
  percentage: number;
}

export interface MachineMoneyMetrics {
  total_spend_sats: number;
  total_spend_msat: number;
  total_fee_sats: number;
  fiat_spend_usd_estimate: number;
  settled_count: number;
  pending_count: number;
  failed_count: number;
  total_transactions: number;
  autonomous_count: number;
  human_approval_count: number;
  autonomous_rate_percentage: number;
  average_settlement_latency_ms: number;
  average_settlement_latency_seconds: number;
  vendor_spend: VendorSpendItem[];
  total_quotes_generated: number;
  quotes_converted: number;
  quote_to_payment_conversion_rate: number;
  computed_at: string;
}

export interface IndustrialPlantAssumptions {
  plant_id: string;
  equipment_tag: string;
  equipment_name: string;
  criticality_tier: string;
  hourly_downtime_cost_usd: number;
  unmitigated_downtime_hours: number;
  catastrophic_failure_probability: number;
  manual_procurement_hours: number;
  autonomous_m2m_dispatch_seconds: number;
  default_intervention_sats: number;
  btc_fiat_usd_rate: number;
  data_basis: string;
  assumptions_version: string;
}

export interface IndustrialEconomicsModel {
  is_estimated: boolean;
  estimated_marker: string;
  calculation_version: string;
  equipment_tag: string;
  equipment_name: string;
  downtime_hours_avoided: number;
  hourly_downtime_cost_usd: number;
  estimated_downtime_exposure_usd: number;
  risk_weighted_exposure_usd: number;
  intervention_cost_sats: number;
  intervention_cost_usd: number;
  net_value_preserved_usd: number;
  protection_multiple: number;
  lead_time_saved_hours: number;
  assumptions: IndustrialPlantAssumptions;
  formula: string;
  risk_weighted_formula: string;
  data_basis: string;
  transparency_notes: string;
  computed_at: string;
}

export interface IndustrialEconomicsRequest {
  equipment_tag?: string;
  intervention_cost_sats?: number;
  hourly_downtime_cost_usd?: number;
  unmitigated_downtime_hours?: number;
}

export async function getMachineMoneyMetrics(): Promise<MachineMoneyMetrics> {
  const res = await fetch(`${API_URL}/api/machine-money/analytics/metrics`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load Machine Money analytics metrics.");
  return res.json();
}

export async function getIndustrialEconomics(
  equipmentTag: string = "P-101A",
  interventionCostSats?: number,
  hourlyCostUsd?: number,
  downtimeHours?: number
): Promise<IndustrialEconomicsModel> {
  const params = new URLSearchParams({ equipment_tag: equipmentTag });
  if (interventionCostSats !== undefined) params.append("intervention_cost_sats", interventionCostSats.toString());
  if (hourlyCostUsd !== undefined) params.append("hourly_downtime_cost_usd", hourlyCostUsd.toString());
  if (downtimeHours !== undefined) params.append("unmitigated_downtime_hours", downtimeHours.toString());

  const res = await fetch(`${API_URL}/api/machine-money/analytics/economics?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load industrial economics data.");
  return res.json();
}

export async function calculateCustomIndustrialEconomics(
  req: IndustrialEconomicsRequest
): Promise<IndustrialEconomicsModel> {
  const res = await fetch(`${API_URL}/api/machine-money/analytics/economics`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error("Failed to calculate custom economics.");
  return res.json();
}

export async function getPlantAssumptions(equipmentTag: string): Promise<IndustrialPlantAssumptions> {
  const res = await fetch(`${API_URL}/api/machine-money/analytics/assumptions/${encodeURIComponent(equipmentTag)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to load plant assumptions for ${equipmentTag}.`);
  return res.json();
}

export interface ProviderStatusResponse {
  provider_name: string;
  provider_mode: "MOCK" | "LIVE";
  network: string;
  settlement_source: "SIMULATED" | "LIGHTNING_NODE";
  is_live: boolean;
  is_connected: boolean;
  balance_sats?: number;
  node_pubkey?: string;
  latency_ms?: number;
  details?: Record<string, any>;
}

export async function getProviderStatus(): Promise<ProviderStatusResponse> {
  const res = await fetch(`${API_URL}/api/machine-money/provider-status`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load provider status.");
  return res.json();
}






