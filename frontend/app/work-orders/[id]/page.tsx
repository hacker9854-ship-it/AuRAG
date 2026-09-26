"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeftIcon } from "lucide-react";

import WorkOrderEditor from "@/components/work-orders/WorkOrderEditor";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  decideWorkOrder,
  getWorkOrder,
  updateWorkOrder,
  type WorkOrderRecord,
} from "@/lib/api";

export default function WorkOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const workOrderId = decodeURIComponent(params.id);
  const [workOrder, setWorkOrder] = useState<WorkOrderRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getWorkOrder(workOrderId)
      .then((result) => {
        if (active) setWorkOrder(result);
      })
      .catch((reason) => {
        if (active) setError(reason instanceof Error ? reason.message : "Work order is unavailable.");
      });
    return () => {
      active = false;
    };
  }, [workOrderId]);

  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1200px] flex-col gap-5 p-4 sm:p-6">
        <Button
          variant="ghost"
          className="w-fit"
          nativeButton={false}
          render={<Link href="/work-orders" />}
        >
          <ArrowLeftIcon data-icon="inline-start" />
          Back to work orders
        </Button>

        {error ? (
          <div className="rounded-xl border p-6 text-sm text-destructive">{error}</div>
        ) : workOrder ? (
          <WorkOrderEditor
            key={`${workOrder.id}-${workOrder.version}`}
            workOrder={workOrder}
            onSave={async (payload) => {
              const updated = await updateWorkOrder(workOrder.id, payload);
              setWorkOrder(updated);
              return updated;
            }}
            onDecision={async (payload) => {
              const updated = await decideWorkOrder(workOrder.id, payload);
              setWorkOrder(updated);
              return updated;
            }}
          />
        ) : (
          <Skeleton className="h-[520px] rounded-xl" />
        )}
    </div>
  );
}
