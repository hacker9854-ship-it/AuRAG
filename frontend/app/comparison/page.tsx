"use client";

import { useState } from "react";
import { AlertTriangleIcon, GitCompareArrowsIcon, SparklesIcon } from "lucide-react";

import ComparisonWorkspace from "@/components/comparison/ComparisonWorkspace";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { postComparison, type ComparisonResponse } from "@/lib/api";

const suggestedQuery = "Why did P-101 fail in March 2025, and which maintenance action should prevent recurrence?";

export default function ComparisonPage() {
  const [query, setQuery] = useState(suggestedQuery);
  const [result, setResult] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function runComparison(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;

    setSubmitting(true);
    setError(null);
    try {
      setResult(await postComparison(cleanQuery));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Comparison is unavailable.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-6">
        <section className="flex flex-col gap-2">
          <Badge variant="info" className="w-fit">
            <GitCompareArrowsIcon data-icon="inline-start" />
            Evaluation workspace
          </Badge>
          <h1 className="font-heading text-xl font-semibold tracking-tight sm:text-2xl">
            GraphRAG versus dense-only RAG
          </h1>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Ask one question against both retrieval paths. The answers, citations, contexts, latency, and graph
            evidence stay independent so the comparison remains technically honest.
          </p>
        </section>

        <Card>
          <CardHeader>
            <CardTitle>Shared evaluation question</CardTitle>
            <CardDescription>Use a relationship-heavy operational question to expose the graph advantage.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={runComparison}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="comparison-query">Question</FieldLabel>
                  <Textarea
                    id="comparison-query"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    rows={3}
                  />
                  <FieldDescription>
                    Both systems receive the exact same question and generate separate answers.
                  </FieldDescription>
                </Field>
                <Button type="submit" disabled={submitting || !query.trim()} className="w-fit">
                  {submitting ? (
                    <Spinner data-icon="inline-start" />
                  ) : (
                    <SparklesIcon data-icon="inline-start" />
                  )}
                  {submitting ? "Running both paths" : "Run comparison"}
                </Button>
              </FieldGroup>
            </form>
          </CardContent>
        </Card>

        {error ? (
          <Alert variant="destructive">
            <AlertTriangleIcon />
            <AlertTitle>Comparison failed</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        {result ? <ComparisonWorkspace data={result} /> : null}
    </div>
  );
}
