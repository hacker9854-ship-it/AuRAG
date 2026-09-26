"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  ArrowUpRightIcon,
  BotIcon,
  SearchIcon,
  SendIcon,
  SparklesIcon,
  TriangleAlertIcon,
} from "lucide-react";
import { ChatError, ChatResponse, getRagasScore, postChat } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
} from "@/components/ui/input-group";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Spinner } from "@/components/ui/spinner";

interface Message {
  role: "user" | "assistant" | "error";
  text: string;
  response?: ChatResponse;
}

const MAX_POLL_ATTEMPTS = 90;

const STARTER_QUERIES = [
  "Why did P-101 fail in March 2025?",
  "Which procedures and clauses govern P-101?",
  "Show recurring failure patterns across the plant.",
];

function qualityTone(score: number) {
  if (score >= 0.7) return "bg-success";
  if (score >= 0.5) return "bg-warning";
  return "bg-destructive";
}

function QualityMetric({ label, score }: { label: string; score: number }) {
  const percentage = Math.round(score * 100);

  return (
    <div className="rounded-md border bg-background/70 p-2.5">
      <div className="flex items-center justify-between gap-2 text-xs">
        <span className="text-muted-foreground">{label}</span>
        <strong className="data-mono font-semibold">{percentage}%</strong>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
        <div className={`h-full rounded-full ${qualityTone(score)}`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

export default function ChatPanel({
  selectedScoreId,
  onSelectMessage,
  onSelectFromCitation,
  onScoreUpdate,
}: {
  selectedScoreId: string | null;
  onSelectMessage: (response: ChatResponse) => void;
  onSelectFromCitation: (response: ChatResponse) => void;
  onScoreUpdate: (response: ChatResponse) => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;
    return () => {
      cancelledRef.current = true;
    };
  }, []);

  function applyScore(scoreId: string, patch: Partial<ChatResponse>) {
    setMessages((items) =>
      items.map((item) =>
        item.response?.score_id === scoreId
          ? { ...item, response: { ...item.response, ...patch } as ChatResponse }
          : item
      )
    );
  }

  async function pollScore(response: ChatResponse) {
    if (!response.score_id) return;
    const scoreId = response.score_id;
    for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      if (cancelledRef.current) return;
      try {
        const result = await getRagasScore(scoreId);
        if (cancelledRef.current) return;
        if (result.ragas_status === "scoring") continue;
        const patch = {
          ragas_status: result.ragas_status,
          ragas_scores: result.ragas_scores,
          low_faithfulness: result.low_faithfulness,
        };
        applyScore(scoreId, patch);
        onScoreUpdate({ ...response, ...patch });
        return;
      } catch {
        if (cancelledRef.current) return;
        const patch = { ragas_status: "error" as const, ragas_scores: {}, low_faithfulness: false };
        applyScore(scoreId, patch);
        onScoreUpdate({ ...response, ...patch });
        return;
      }
    }
    if (cancelledRef.current) return;
    const patch = { ragas_status: "scoring_delayed" as const };
    applyScore(scoreId, patch);
    onScoreUpdate({ ...response, ...patch });
  }

  async function send() {
    const query = input.trim();
    if (!query || pending) return;
    setInput("");
    setMessages((items) => [...items, { role: "user", text: query }]);
    setPending(true);
    try {
      const response = await postChat(query);
      setMessages((items) => [...items, { role: "assistant", text: response.agent_response, response }]);
      onSelectMessage(response);
      void pollScore(response);
    } catch (err) {
      const detail = err instanceof ChatError ? err.message : "Something went wrong. Please try again.";
      setMessages((items) => [...items, { role: "error", text: detail }]);
    } finally {
      setPending(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void send();
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ScrollArea className="min-h-0 flex-1">
        <div className="min-h-full p-4">
          {messages.length === 0 && (
            <Empty className="min-h-[430px] border-0 p-4">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <SparklesIcon />
                </EmptyMedia>
                <EmptyTitle>Start with an operational question</EmptyTitle>
                <EmptyDescription>
                  AuRAG can trace failures across work orders, procedures, people, documents, and regulatory clauses.
                </EmptyDescription>
              </EmptyHeader>
              <EmptyContent className="max-w-xl">
                <div className="grid w-full gap-2">
                  {STARTER_QUERIES.map((query) => (
                    <Button
                      key={query}
                      type="button"
                      variant="outline"
                      className="h-auto w-full justify-start py-3 text-left whitespace-normal"
                      onClick={() => setInput(query)}
                    >
                      <SearchIcon data-icon="inline-start" />
                      {query}
                    </Button>
                  ))}
                </div>
              </EmptyContent>
            </Empty>
          )}

          {messages.map((message, index) => {
            if (message.role === "error") {
              return (
                <Alert key={`${message.role}-${index}`} variant="destructive" className="mb-3">
                  <AlertTitle>Service unavailable</AlertTitle>
                  <AlertDescription>{message.text}</AlertDescription>
                </Alert>
              );
            }

            const isSelected = !!message.response && message.response.score_id === selectedScoreId;
            const scoring = message.response?.ragas_status === "scoring";
            const scoringDelayed = message.response?.ragas_status === "scoring_delayed";
            const isInteractive = !!message.response;

            return (
              <div
                key={`${message.role}-${index}`}
                role={isInteractive ? "button" : undefined}
                tabIndex={isInteractive ? 0 : undefined}
                onClick={() => message.response && onSelectMessage(message.response)}
                onKeyDown={(event) => {
                  if (message.response && (event.key === "Enter" || event.key === " ")) {
                    event.preventDefault();
                    onSelectMessage(message.response);
                  }
                }}
                className={cn(
                  "mb-3 w-[min(94%,48rem)] rounded-lg border bg-card p-4 text-sm shadow-xs transition-colors",
                  isInteractive && "hover:bg-muted/40",
                  message.role === "user" && "ml-auto w-[min(88%,40rem)] bg-muted",
                  isSelected && "border-primary bg-primary/5 ring-1 ring-primary/20"
                )}
              >
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="text-xs font-medium text-muted-foreground">
                    {message.role === "user" ? "Operator" : "AuRAG agent"}
                  </span>
                  {isSelected && <Badge variant="warning">Driving evidence</Badge>}
                </div>

                <div className="flex items-start gap-3">
                  {message.role === "assistant" && (
                    <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary/12 text-primary">
                      <BotIcon className="size-4" />
                    </div>
                  )}
                  <p className="min-w-0 flex-1 whitespace-pre-wrap leading-6">{message.text}</p>
                </div>

                {message.response && (
                  <div className="mt-3 flex flex-col gap-2 border-t pt-3">
                    <div className="flex flex-wrap gap-1.5">
                      <Badge variant="warning">{message.response.routed_agent}</Badge>
                      <Badge variant="outline">
                        {message.response.intent} / {(message.response.routing_confidence * 100).toFixed(0)}%
                      </Badge>
                      {scoring && <Badge variant="info">Quality scoring</Badge>}
                      {scoringDelayed && <Badge variant="warning">Scoring delayed</Badge>}
                      {message.response.ragas_status === "error" && (
                        <Badge variant="destructive">Quality unavailable</Badge>
                      )}
                    </div>
                    {message.response.ragas_status === "scored" && (
                      <div className="grid gap-2 sm:grid-cols-3">
                        {message.response.ragas_scores.faithfulness !== undefined && (
                          <QualityMetric
                            label="Faithfulness"
                            score={message.response.ragas_scores.faithfulness}
                          />
                        )}
                        {message.response.ragas_scores.context_precision !== undefined && (
                          <QualityMetric
                            label="Context precision"
                            score={message.response.ragas_scores.context_precision}
                          />
                        )}
                        {message.response.ragas_scores.answer_relevancy !== undefined && (
                          <QualityMetric
                            label="Answer relevancy"
                            score={message.response.ragas_scores.answer_relevancy}
                          />
                        )}
                      </div>
                    )}
                    {message.response.low_faithfulness && (
                      <Alert variant="destructive" className="py-2.5">
                        <TriangleAlertIcon />
                        <AlertTitle>Low evidence faithfulness</AlertTitle>
                        <AlertDescription>
                          Treat this answer as unverified and inspect its cited graph trail before acting.
                        </AlertDescription>
                      </Alert>
                    )}
                    {message.response.citations.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {message.response.citations.map((citation) => (
                          <Button
                            key={citation}
                            type="button"
                            variant="ghost"
                            size="xs"
                            className="h-auto max-w-full whitespace-normal"
                            onClick={(event) => {
                              event.stopPropagation();
                              if (message.response) onSelectFromCitation(message.response);
                            }}
                          >
                            <ArrowUpRightIcon data-icon="inline-start" />
                            {citation}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {pending && (
            <div className="flex items-center gap-2 rounded-lg border bg-muted/40 p-3 text-sm text-muted-foreground" aria-live="polite">
              <Spinner />
              Building an evidence-backed answer
            </div>
          )}
        </div>
      </ScrollArea>

      <form className="shrink-0 border-t bg-card p-3" onSubmit={handleSubmit}>
        <FieldGroup className="gap-2">
          <Field>
            <FieldLabel htmlFor="operational-question" className="sr-only">
              Operational question
            </FieldLabel>
            <InputGroup className="h-11 bg-background">
              <InputGroupInput
                id="operational-question"
                aria-label="Operational question"
                placeholder="Why did P-101 fail in March 2025?"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                disabled={pending}
              />
              <InputGroupAddon align="inline-end">
                <InputGroupButton
                  type="submit"
                  size="icon-sm"
                  variant="default"
                  disabled={pending || !input.trim()}
                  aria-label={pending ? "Routing question" : "Send question"}
                >
                  {pending ? <Spinner data-icon="inline-start" /> : <SendIcon data-icon="inline-start" />}
                </InputGroupButton>
              </InputGroupAddon>
            </InputGroup>
          </Field>
        </FieldGroup>
      </form>
    </div>
  );
}
