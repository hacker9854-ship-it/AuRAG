"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeftIcon } from "lucide-react";

import WorkOrderEditor from "@/components/work-orders/WorkOrderEditor";
import { Button, buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  decideWorkOrder,
  getWorkOrder,
  updateWorkOrder,
  type WorkOrderRecord,
} from "@/lib/api";

export default function WorkOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const rawId = params?.id ? decodeURIComponent(params.id) : "";
  const workOrderId = rawId.trim().replace(/\s+/g, "-");
  const [workOrder, setWorkOrder] = useState<WorkOrderRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    if (!workOrderId) {
      setError("No work order ID specified.");
      setLoading(false);
      return;
    }
    getWorkOrder(workOrderId)
      .then((result) => {
        if (active) {
          if (result && result.id) {
            setWorkOrder(result);
          } else {
            setError(`Work order ${workOrderId} could not be loaded.`);
          }
        }
      })
      .catch((reason) => {
        if (active) setError(reason instanceof Error ? reason.message : "Work order is unavailable.");
      })
      .finally(() => {
        if (active) setLoading(false);
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

        {loading ? (
          <Skeleton className="h-[520px] rounded-xl" />
        ) : error ? (
          <div className="flex flex-col gap-4 rounded-xl border border-destructive/20 bg-destructive/10 p-6 text-sm text-destructive">
            <p className="font-semibold">{error}</p>
            <div className="flex flex-wrap gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  getWorkOrder("WO-2026-003").then(setWorkOrder).catch(() => {});
                  setError(null);
                }}
              >
                Load Sample Work Order (WO-2026-003)
              </Button>
              <Link href="/work-orders" className={buttonVariants({ variant: "ghost", size: "sm" })}>
                View all work orders
              </Link>
            </div>
          </div>
        ) : workOrder && workOrder.id ? (
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
