"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRightIcon, ClipboardListIcon, RefreshCwIcon } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { getWorkOrders, type WorkOrderRecord } from "@/lib/api";

const statuses = ["All", "Draft", "In Review", "Approved", "Rejected", "Open", "Closed", "Overdue"];

export default function WorkOrdersPage() {
  const [status, setStatus] = useState("All");
  const [items, setItems] = useState<WorkOrderRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    getWorkOrders(status === "All" ? undefined : status)
      .then((result) => {
        if (active) setItems(result);
      })
      .catch((reason) => {
        if (active) setError(reason instanceof Error ? reason.message : "Work orders are unavailable.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [status, reloadKey]);

  function changeStatus(value: string | null) {
    if (!value) return;
    setLoading(true);
    setError(null);
    setStatus(value);
  }

  function refresh() {
    setLoading(true);
    setError(null);
    setReloadKey((value) => value + 1);
  }

  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-6">
        <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="flex flex-col gap-1">
            <h1 className="font-heading text-xl font-semibold tracking-tight sm:text-2xl">Work-order decisions</h1>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Review predictive drafts, preserve edits and decisions, and inspect the resulting audit history.
            </p>
          </div>
          <div className="flex gap-2">
            <Select value={status} onValueChange={changeStatus}>
              <SelectTrigger aria-label="Work-order status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {statuses.map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={refresh} disabled={loading}>
              <RefreshCwIcon data-icon="inline-start" />
              Refresh
            </Button>
          </div>
        </section>

        {error ? (
          <Card>
            <CardHeader>
              <CardTitle>Work orders unavailable</CardTitle>
              <CardDescription>{error}</CardDescription>
            </CardHeader>
          </Card>
        ) : loading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }, (_, index) => (
              <Skeleton key={index} className="h-48 rounded-xl" />
            ))}
          </div>
        ) : items.length ? (
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" aria-label="Work orders">
            {items.map((item) => (
              <Card key={item.id}>
                <CardHeader>
                  <CardTitle>{item.id}</CardTitle>
                  <CardDescription>
                    {item.equipment} · {item.type} · version {item.version ?? 0}
                  </CardDescription>
                  <CardAction>
                    <Badge variant="outline">{item.status}</Badge>
                  </CardAction>
                </CardHeader>
                <CardContent className="flex flex-col gap-4">
                  <p className="line-clamp-3 text-sm leading-6 text-muted-foreground">{item.description}</p>
                  <Link
                    className={buttonVariants({ variant: "outline" })}
                    href={`/work-orders/${encodeURIComponent(item.id)}`}
                  >
                    Review work order
                    <ArrowRightIcon data-icon="inline-end" />
                  </Link>
                </CardContent>
              </Card>
            ))}
          </section>
        ) : (
          <Card>
            <CardContent>
              <Empty>
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <ClipboardListIcon />
                  </EmptyMedia>
                  <EmptyTitle>No work orders match this filter</EmptyTitle>
                  <EmptyDescription>
                    Predictive drafts appear here as soon as a warning is converted into an intervention.
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
            </CardContent>
          </Card>
        )}
    </div>
  );
}
