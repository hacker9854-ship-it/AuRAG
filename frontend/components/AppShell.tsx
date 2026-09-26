"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import AppSidebar from "@/components/AppSidebar";
import DashboardHeader from "@/components/DashboardHeader";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { getReadiness, type ReadinessResponse } from "@/lib/api";

const routeTitles: Array<[prefix: string, title: string]> = [
  ["/work-orders/", "Work Order"],
  ["/work-orders", "Work Orders"],
  ["/predictive-watch", "Predictive Watch"],
  ["/knowledge-risk", "Knowledge Risk"],
  ["/comparison", "RAG Comparison"],
  ["/evaluation", "Evaluation"],
  ["/investigate", "Investigate"],
  ["/", "Command Center"],
];

export function getWorkspaceTitle(pathname: string) {
  return routeTitles.find(([prefix]) =>
    prefix === "/" ? pathname === "/" : pathname.startsWith(prefix),
  )?.[1] ?? "Workspace";
}

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);

  useEffect(() => {
    let active = true;

    async function refresh() {
      try {
        const next = await getReadiness();
        if (active) setReadiness(next);
      } catch {
        if (active) {
          setReadiness({
            status: "degraded",
            ready: false,
            dependencies: {
              backend: { status: "down", detail: "Backend is unreachable." },
            },
          });
        }
      }
    }

    void refresh();
    const interval = window.setInterval(refresh, 30_000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <SidebarProvider defaultOpen>
      <AppSidebar readiness={readiness} />
      <SidebarInset className="h-svh min-w-0 overflow-hidden">
        <DashboardHeader title={getWorkspaceTitle(pathname)} readiness={readiness} />
        <ScrollArea className="min-h-0 flex-1">
          <div className="aurag-grid min-h-full">{children}</div>
        </ScrollArea>
      </SidebarInset>
    </SidebarProvider>
  );
}
