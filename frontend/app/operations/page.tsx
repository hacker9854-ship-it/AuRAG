"use client";

import React, { useEffect, useState } from "react";
import {
  AlertTriangleIcon,
  CheckCircle2Icon,
  ClockIcon,
  DatabaseIcon,
  FileCheck2Icon,
  PlayIcon,
  RefreshCwIcon,
  RotateCcwIcon,
  ShieldAlertIcon,
  ShieldCheckIcon,
  SlidersIcon,
  XCircleIcon,
  ZapIcon,
} from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  evaluateAutomation,
  getApprovalQueue,
  getAutomationPolicies,
  getRemediations,
  reviewApproval,
  updateRemediationStatus,
  type ApprovalRecord,
  type AutomationPolicy,
  type EvaluationRemediation,
} from "@/lib/api";

export default function OperationsPage() {
  const [activeTab, setActiveTab] = useState<"queue" | "policies" | "simulator" | "remediations">("queue");
  const [loading, setLoading] = useState(true);
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [policies, setPolicies] = useState<AutomationPolicy[]>([]);
  const [remediations, setRemediations] = useState<EvaluationRemediation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Simulator state
  const [simEquipment, setSimEquipment] = useState("P-101A");
  const [simTrigger, setSimTrigger] = useState("HEALTH_INDEX_CRITICAL");
  const [simHealth, setSimHealth] = useState(35);
  const [simVibration, setSimVibration] = useState(5.8);
  const [simResult, setSimResult] = useState<any | null>(null);
  const [simLoading, setSimLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [queueRes, polRes, remRes] = await Promise.all([
        getApprovalQueue(),
        getAutomationPolicies(),
        getRemediations(),
      ]);
      setApprovals(queueRes.queue || []);
      setPolicies(polRes.policies || []);
      setRemediations(remRes.remediations || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load operational data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApproval = async (approvalId: string, action: "APPROVED" | "REJECTED") => {
    try {
      await reviewApproval(approvalId, action, `Reviewed by lead engineer on console`);
      setSuccessMsg(`Action ${action} successfully submitted for approval ${approvalId}.`);
      setApprovals((prev) =>
        prev.map((a) =>
          a.approval_id === approvalId
            ? { ...a, status: action, reviewed_by: "current-user" }
            : a
        )
      );
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err?.message || "Failed to submit approval");
    }
  };

  const handleSimulate = async (dryRun: boolean = true) => {
    setSimLoading(true);
    setSimResult(null);
    try {
      const contextData: Record<string, any> = {
        equipment_tag: simEquipment,
      };
      if (simTrigger === "HEALTH_INDEX_CRITICAL") {
        contextData.health_index = Number(simHealth);
        contextData.reason = `Health score dropped to ${simHealth}`;
      } else if (simTrigger === "VIBRATION_SPIKE") {
        contextData.vibration_mms = Number(simVibration);
        contextData.reason = `Bearing vibration excursion (${simVibration} mm/s)`;
      } else if (simTrigger === "STATUTORY_OVERDUE") {
        contextData.audit_status = "AUDIT_FAILED_GAPS_FOUND";
        contextData.status = "OVERDUE";
        contextData.clause_id = "FACT-1948-SEC-31";
      }

      const res = await evaluateAutomation({
        trigger_type: simTrigger,
        context_data: contextData,
        dry_run: dryRun,
      });
      setSimResult(res);
      if (!dryRun) {
        fetchData();
      }
    } catch (err: any) {
      setError(err?.message || "Simulation failed");
    } finally {
      setSimLoading(false);
    }
  };

  const handleRemediationStatus = async (remId: string, status: "REINDEXED" | "RESOLVED") => {
    try {
      await updateRemediationStatus(remId, status);
      setRemediations((prev) =>
        prev.map((r) => (r.remediation_id === remId ? { ...r, status } : r))
      );
    } catch (err: any) {
      setError(err?.message || "Failed to update remediation status");
    }
  };

  return (
    <div className="flex-1 space-y-6 p-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Operations & Governance Hub
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Human-in-the-loop SAP PM & QMS automations, approval queues, dry-run simulation, and remediation.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={loading} className="gap-2">
          <RefreshCwIcon className={`size-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Notifications */}
      {successMsg && (
        <Alert className="border-emerald-500/50 bg-emerald-50/70 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-200">
          <CheckCircle2Icon className="size-4 text-emerald-600 dark:text-emerald-400" />
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>{successMsg}</AlertDescription>
        </Alert>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertTriangleIcon className="size-4" />
          <AlertTitle>Operation Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 gap-4">
        <button
          onClick={() => setActiveTab("queue")}
          className={`pb-3 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "queue"
              ? "border-blue-600 text-blue-600 dark:text-blue-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          <ClockIcon className="size-4" />
          Pending Approvals ({approvals.filter((a) => a.status === "PENDING").length})
        </button>
        <button
          onClick={() => setActiveTab("policies")}
          className={`pb-3 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "policies"
              ? "border-blue-600 text-blue-600 dark:text-blue-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          <SlidersIcon className="size-4" />
          Automation Policies ({policies.length})
        </button>
        <button
          onClick={() => setActiveTab("simulator")}
          className={`pb-3 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "simulator"
              ? "border-blue-600 text-blue-600 dark:text-blue-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          <ZapIcon className="size-4" />
          Dry-Run Policy Simulator
        </button>
        <button
          onClick={() => setActiveTab("remediations")}
          className={`pb-3 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "remediations"
              ? "border-blue-600 text-blue-600 dark:text-blue-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          <FileCheck2Icon className="size-4" />
          Evaluation Remediation ({remediations.filter((r) => r.status === "PENDING_REINDEX").length})
        </button>
      </div>

      {/* Tab 1: Approval Queue */}
      {activeTab === "queue" && (
        <div className="space-y-4">
          {approvals.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-slate-500">
                <CheckCircle2Icon className="mx-auto size-10 text-emerald-500 mb-2 opacity-80" />
                <p className="font-medium">All approval queues are clear</p>
                <p className="text-xs text-slate-400">No automated actions are currently awaiting operator signoff.</p>
              </CardContent>
            </Card>
          ) : (
            approvals.map((item) => (
              <Card key={item.approval_id} className="overflow-hidden border border-slate-200 dark:border-slate-800">
                <CardHeader className="bg-slate-50/50 dark:bg-slate-900/50 py-3 px-6 flex flex-row items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-semibold text-slate-500">{item.approval_id}</span>
                    <Badge
                      variant={
                        item.status === "PENDING"
                          ? "outline"
                          : item.status === "APPROVED" || item.status === "AUTONOMOUS_EXECUTED"
                          ? "default"
                          : "destructive"
                      }
                      className="text-xs"
                    >
                      {item.status}
                    </Badge>
                    <Badge variant="secondary" className="text-xs font-mono">
                      {item.target_system}
                    </Badge>
                  </div>
                  <span className="text-xs text-slate-400">{item.created_at ? new Date(item.created_at).toLocaleString() : ""}</span>
                </CardHeader>
                <CardContent className="p-6 space-y-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-base text-slate-900 dark:text-slate-100">
                        {String(item.payload?.title || item.action_type)}
                      </h3>
                      <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
                        {String(item.payload?.description || item.payload?.issue_summary || "Automated draft staged.")}
                      </p>
                    </div>
                  </div>

                  {/* Target Payload Preview */}
                  <div className="bg-slate-950 text-slate-100 p-3 rounded-lg text-xs font-mono overflow-x-auto">
                    <pre>{JSON.stringify(item.payload, null, 2)}</pre>
                  </div>

                  {/* Rollback Guidance */}
                  {item.rollback_guidance && (
                    <div className="p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40 rounded-lg flex items-start gap-2 text-xs text-amber-900 dark:text-amber-200">
                      <RotateCcwIcon className="size-4 shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
                      <div>
                        <span className="font-semibold">Deterministic Rollback Procedure: </span>
                        {item.rollback_guidance}
                      </div>
                    </div>
                  )}

                  {/* Action Controls */}
                  {item.status === "PENDING" && (
                    <div className="flex justify-end gap-3 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 border-red-200 hover:bg-red-50 dark:hover:bg-red-950/40"
                        onClick={() => handleApproval(item.approval_id, "REJECTED")}
                      >
                        <XCircleIcon className="size-4 mr-1.5" />
                        Reject Action
                      </Button>
                      <Button
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                        onClick={() => handleApproval(item.approval_id, "APPROVED")}
                      >
                        <CheckCircle2Icon className="size-4 mr-1.5" />
                        Approve & Dispatch
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Tab 2: Policies */}
      {activeTab === "policies" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {policies.map((p) => (
            <Card key={p.policy_id} className="border border-slate-200 dark:border-slate-800">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-slate-400">{p.policy_id}</span>
                  <Badge variant={p.approval_threshold === "AUTONOMOUS" ? "secondary" : "outline"} className="text-xs">
                    {p.approval_threshold}
                  </Badge>
                </div>
                <CardTitle className="text-base font-semibold mt-1">{p.name}</CardTitle>
                <CardDescription className="text-xs">{p.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Trigger Type:</span>
                  <span className="font-mono font-medium">{p.trigger_type}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Action:</span>
                  <span className="font-mono font-medium">{p.action_type}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Target System:</span>
                  <span className="font-medium">{p.target_system}</span>
                </div>
                <div className="mt-2 text-slate-500">
                  <span className="font-semibold block mb-1">Rollback Guidance:</span>
                  <p className="font-mono text-[11px] bg-slate-50 dark:bg-slate-900 p-2 rounded border border-slate-100 dark:border-slate-800">
                    {p.rollback_guidance || "Standard SAP/QMS archival"}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Tab 3: Simulator */}
      {activeTab === "simulator" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <PlayIcon className="size-5 text-blue-600" />
                Dry-Run Policy Simulator
              </CardTitle>
              <CardDescription>
                Test automation policies in safe dry-run mode without committing changes or modifying target SAP/QMS databases.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1.5">
                    Equipment Tag
                  </label>
                  <Input value={simEquipment} onChange={(e) => setSimEquipment(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1.5">
                    Trigger Type
                  </label>
                  <select
                    className="w-full h-9 rounded-md border border-slate-200 dark:border-slate-800 bg-background px-3 py-1 text-sm shadow-sm"
                    value={simTrigger}
                    onChange={(e) => setSimTrigger(e.target.value)}
                  >
                    <option value="HEALTH_INDEX_CRITICAL">HEALTH_INDEX_CRITICAL</option>
                    <option value="VIBRATION_SPIKE">VIBRATION_SPIKE</option>
                    <option value="STATUTORY_OVERDUE">STATUTORY_OVERDUE</option>
                  </select>
                </div>

                {simTrigger === "HEALTH_INDEX_CRITICAL" && (
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1.5">
                      Simulated Health Index (0-100)
                    </label>
                    <Input
                      type="number"
                      value={simHealth}
                      onChange={(e) => setSimHealth(Number(e.target.value))}
                    />
                  </div>
                )}
                {simTrigger === "VIBRATION_SPIKE" && (
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1.5">
                      Simulated Vibration (mm/s)
                    </label>
                    <Input
                      type="number"
                      step="0.1"
                      value={simVibration}
                      onChange={(e) => setSimVibration(Number(e.target.value))}
                    />
                  </div>
                )}
              </div>

              <div className="flex gap-3 pt-2">
                <Button onClick={() => handleSimulate(true)} disabled={simLoading} className="gap-2">
                  <PlayIcon className="size-4" />
                  Run Safe Simulation (Dry-Run)
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleSimulate(false)}
                  disabled={simLoading}
                  className="gap-2 text-amber-600 border-amber-200 hover:bg-amber-50 dark:hover:bg-amber-950/40"
                >
                  <ZapIcon className="size-4" />
                  Live Trigger Test
                </Button>
              </div>

              {simResult && (
                <div className="mt-6 space-y-4">
                  <h4 className="font-semibold text-sm flex items-center gap-2">
                    Simulation Output:
                    <Badge variant={simResult.dry_run ? "outline" : "default"}>
                      {simResult.dry_run ? "DRY-RUN SIMULATION" : "LIVE EXECUTED"}
                    </Badge>
                  </h4>
                  <div className="bg-slate-950 text-slate-100 p-4 rounded-lg text-xs font-mono overflow-x-auto">
                    <pre>{JSON.stringify(simResult, null, 2)}</pre>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 4: Evaluation Remediations */}
      {activeTab === "remediations" && (
        <div className="space-y-4">
          {remediations.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-slate-500">
                <CheckCircle2Icon className="mx-auto size-10 text-emerald-500 mb-2 opacity-80" />
                <p className="font-medium">No evaluation remediation items pending</p>
                <p className="text-xs text-slate-400">Flagged answers from the Evaluation dashboard appear here for human correction.</p>
              </CardContent>
            </Card>
          ) : (
            remediations.map((rem) => (
              <Card key={rem.remediation_id} className="border border-slate-200 dark:border-slate-800">
                <CardHeader className="py-3 px-6 flex flex-row items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-semibold">{rem.remediation_id}</span>
                    <Badge variant={rem.status === "RESOLVED" ? "default" : "outline"} className="text-xs">
                      {rem.status}
                    </Badge>
                    <span className="text-xs text-slate-500 font-mono">Score Ref: {rem.score_id}</span>
                  </div>
                  <span className="text-xs text-slate-400">{rem.created_at ? new Date(rem.created_at).toLocaleDateString() : ""}</span>
                </CardHeader>
                <CardContent className="p-6 space-y-3 text-sm">
                  <div>
                    <span className="font-semibold text-slate-700 dark:text-slate-300">Operator Reason: </span>
                    <span className="text-slate-900 dark:text-slate-100">{rem.reason}</span>
                  </div>
                  <div className="bg-amber-50 dark:bg-amber-950/30 p-3 rounded border border-amber-200 dark:border-amber-900/30 text-xs">
                    <span className="font-semibold text-amber-900 dark:text-amber-200 block mb-1">Correction Notes:</span>
                    <p className="text-amber-800 dark:text-amber-300">{rem.correction_notes}</p>
                  </div>
                  {rem.status === "PENDING_REINDEX" && (
                    <div className="flex justify-end gap-2 pt-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRemediationStatus(rem.remediation_id, "REINDEXED")}
                      >
                        Queue Document Re-indexing
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleRemediationStatus(rem.remediation_id, "RESOLVED")}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        Mark Resolved
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
