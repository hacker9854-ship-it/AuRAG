"use client";

import { useEffect, useState } from "react";
import { AlertTriangleIcon, RefreshCwIcon, ShieldCheckIcon } from "lucide-react";

import EvaluationDashboard from "@/components/evaluation/EvaluationDashboard";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getEvaluationResults,
  getEvaluationSummary,
  type EvaluationPage,
  type EvaluationRecord,
  type EvaluationSummary,
} from "@/lib/api";

const PAGE_SIZE = 20;

export default function EvaluationPage() {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [items, setItems] = useState<EvaluationRecord[]>([]);
  const [pageInfo, setPageInfo] = useState<EvaluationPage>({
    items: [],
    limit: PAGE_SIZE,
    offset: 0,
    total: 0,
    has_more: false,
  });
  const [lowOnly, setLowOnly] = useState(false);
  const [status, setStatus] = useState("all");
  const [agent, setAgent] = useState("all");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      getEvaluationSummary(),
      getEvaluationResults({
        limit: PAGE_SIZE,
        offset,
        status: status === "all" ? undefined : status,
        agent: agent === "all" ? undefined : agent,
        low_faithfulness: lowOnly ? true : undefined,
      }),
    ])
      .then(([summaryResult, historyResult]) => {
        if (!active) return;
        const failures: string[] = [];
        if (summaryResult.status === "fulfilled") {
          setSummary(summaryResult.value);
        } else {
          failures.push(
            summaryResult.reason instanceof Error
              ? summaryResult.reason.message
              : "Evaluation summary is unavailable.",
          );
        }
        if (historyResult.status === "fulfilled") {
          setPageInfo(historyResult.value);
          setItems(historyResult.value.items);
        } else {
          failures.push(
            historyResult.reason instanceof Error
              ? historyResult.reason.message
              : "Evaluation history is unavailable.",
          );
        }
        setError(failures.length ? failures.join(" ") : null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [agent, lowOnly, offset, reloadKey, status]);

  function refresh() {
    setLoading(true);
    setError(null);
    setReloadKey((value) => value + 1);
  }

  function changeQueue(nextLowOnly: boolean) {
    setLoading(true);
    setError(null);
    setOffset(0);
    setLowOnly(nextLowOnly);
  }

  function changeStatus(nextStatus: string) {
    setLoading(true);
    setError(null);
    setOffset(0);
    setStatus(nextStatus);
  }

  function changeAgent(nextAgent: string) {
    setLoading(true);
    setError(null);
    setOffset(0);
    setAgent(nextAgent);
  }

  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-6">
        <section className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="flex flex-col gap-2">
            <Badge variant="success" className="w-fit">
              <ShieldCheckIcon data-icon="inline-start" />
              RAGAS quality controls
            </Badge>
            <h1 className="font-heading text-xl font-semibold tracking-tight sm:text-2xl">
              Answer quality evaluation
            </h1>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Monitor faithfulness, context precision, answer relevancy, scoring failures, and the review queue across
              every grounded answer.
            </p>
          </div>
          <Button variant="outline" onClick={refresh} disabled={loading}>
            <RefreshCwIcon data-icon="inline-start" />
            Refresh
          </Button>
        </section>

        {error ? (
          <Alert variant="destructive">
            <AlertTriangleIcon />
            <AlertTitle>Evaluation dashboard is unavailable</AlertTitle>
            <AlertDescription className="flex flex-col items-start gap-3">
              <span>{error}</span>
              <Button variant="outline" size="sm" onClick={refresh}>
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        ) : null}

        {loading && !summary ? (
          <div className="grid gap-4">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {Array.from({ length: 4 }, (_, index) => (
                <Skeleton key={index} className="h-28 rounded-xl" />
              ))}
            </div>
            <Skeleton className="h-96 rounded-xl" />
          </div>
        ) : summary ? (
          <EvaluationDashboard
            summary={summary}
            items={items}
            total={pageInfo.total}
            offset={pageInfo.offset}
            hasMore={pageInfo.has_more}
            lowOnly={lowOnly}
            status={status}
            agent={agent}
            loading={loading}
            onQueueChange={changeQueue}
            onStatusChange={changeStatus}
            onAgentChange={changeAgent}
            onPrevious={() => {
              setLoading(true);
              setOffset((value) => Math.max(0, value - PAGE_SIZE));
            }}
            onNext={() => {
              setLoading(true);
              setOffset((value) => value + PAGE_SIZE);
            }}
          />
        ) : null}
    </div>
  );
}
