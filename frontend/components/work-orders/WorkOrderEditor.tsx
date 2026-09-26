"use client";

import { useState } from "react";
import { CheckIcon, SaveIcon, XIcon } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import type { WorkOrderRecord } from "@/lib/api";

type SavePayload = {
  expected_version: number;
  description: string;
  recommended_action: string;
};

type DecisionPayload = {
  decision: "accept" | "reject";
  expected_version: number;
  reason?: string | null;
};

const statusVariant = {
  Draft: "warning",
  "In Review": "info",
  Approved: "success",
  Rejected: "destructive",
  Open: "info",
  Closed: "outline",
  Overdue: "destructive",
} as const;

export default function WorkOrderEditor({
  workOrder,
  onSave,
  onDecision,
}: {
  workOrder: WorkOrderRecord;
  onSave: (payload: SavePayload) => Promise<WorkOrderRecord>;
  onDecision: (payload: DecisionPayload) => Promise<WorkOrderRecord>;
}) {
  const [description, setDescription] = useState(workOrder.description);
  const [recommendedAction, setRecommendedAction] = useState(workOrder.recommended_action);
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [pending, setPending] = useState<"save" | "accept" | "reject" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const current = workOrder;
  const editable = current.status === "Draft" || current.status === "In Review";

  async function save() {
    setPending("save");
    setError(null);
    try {
      await onSave({
        expected_version: current.version,
        description,
        recommended_action: recommendedAction,
      });
    } catch (reasonValue) {
      setError(reasonValue instanceof Error ? reasonValue.message : "Work-order update failed.");
    } finally {
      setPending(null);
    }
  }

  async function decide(decision: "accept" | "reject") {
    setPending(decision);
    setError(null);
    try {
      await onDecision({
        decision,
        expected_version: current.version,
        reason: decision === "reject" ? reason.trim() : null,
      });
      setRejecting(false);
    } catch (reasonValue) {
      setError(reasonValue instanceof Error ? reasonValue.message : "Work-order decision failed.");
    } finally {
      setPending(null);
    }
  }

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle>{current.id}</CardTitle>
        <CardDescription>
          {current.equipment} · {current.type} · version {current.version}
        </CardDescription>
        <CardAction>
          <Badge variant={statusVariant[current.status as keyof typeof statusVariant] ?? "outline"}>
            {current.status}
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Work-order action failed</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <FieldGroup className="gap-4">
          <Field data-disabled={!editable}>
            <FieldLabel htmlFor={`description-${current.id}`}>Description</FieldLabel>
            <Textarea
              id={`description-${current.id}`}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              disabled={!editable}
              rows={3}
            />
          </Field>
          <Field data-disabled={!editable}>
            <FieldLabel htmlFor={`action-${current.id}`}>Recommended action</FieldLabel>
            <Textarea
              id={`action-${current.id}`}
              value={recommendedAction}
              onChange={(event) => setRecommendedAction(event.target.value)}
              disabled={!editable}
              rows={3}
            />
          </Field>
          {rejecting && editable ? (
            <Field data-invalid={!reason.trim()}>
              <FieldLabel htmlFor={`reason-${current.id}`}>Rejection reason</FieldLabel>
              <Textarea
                id={`reason-${current.id}`}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                aria-invalid={!reason.trim()}
                rows={2}
              />
            </Field>
          ) : null}
        </FieldGroup>
      </CardContent>
      {editable ? (
        <CardFooter className="flex flex-wrap gap-2 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={save}
            disabled={pending !== null || !description.trim() || !recommendedAction.trim()}
          >
            {pending === "save" ? <Spinner data-icon="inline-start" /> : <SaveIcon data-icon="inline-start" />}
            Save changes
          </Button>
          <Button type="button" onClick={() => decide("accept")} disabled={pending !== null}>
            {pending === "accept" ? <Spinner data-icon="inline-start" /> : <CheckIcon data-icon="inline-start" />}
            Accept
          </Button>
          {rejecting ? (
            <>
              <Button
                type="button"
                variant="destructive"
                onClick={() => decide("reject")}
                disabled={pending !== null || !reason.trim()}
              >
                {pending === "reject" ? <Spinner data-icon="inline-start" /> : <XIcon data-icon="inline-start" />}
                Confirm rejection
              </Button>
              <Button type="button" variant="ghost" onClick={() => setRejecting(false)} disabled={pending !== null}>
                Cancel
              </Button>
            </>
          ) : (
            <Button type="button" variant="destructive" onClick={() => setRejecting(true)} disabled={pending !== null}>
              <XIcon data-icon="inline-start" />
              Reject
            </Button>
          )}
        </CardFooter>
      ) : null}
    </Card>
  );
}
