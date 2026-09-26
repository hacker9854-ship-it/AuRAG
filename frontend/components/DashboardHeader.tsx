"use client";

import { CircleAlertIcon, CircleCheckIcon, FlaskConicalIcon, LoaderCircleIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import NotificationCenter from "@/components/notifications/NotificationCenter";
import type { ReadinessResponse } from "@/lib/api";

export default function DashboardHeader({
  title,
  readiness,
}: {
  title: string;
  readiness: ReadinessResponse | null;
}) {
  return (
    <header className="sticky top-0 flex h-14 shrink-0 items-center justify-between gap-4 border-b bg-background/92 px-4 backdrop-blur sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <SidebarTrigger />
        <Separator orientation="vertical" className="hidden h-4 self-center sm:block" />
        <Breadcrumb className="min-w-0">
          <BreadcrumbList className="flex-nowrap">
            <BreadcrumbItem className="hidden sm:inline-flex">Workspace</BreadcrumbItem>
            <BreadcrumbSeparator className="hidden sm:list-item" />
            <BreadcrumbItem className="min-w-0">
              <BreadcrumbPage className="truncate">{title}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <NotificationCenter />
        <Badge variant="outline" className="hidden sm:inline-flex">
          <FlaskConicalIcon data-icon="inline-start" />
          Demo environment
        </Badge>
        {readiness === null ? (
          <Badge variant="warning">
            <LoaderCircleIcon className="animate-spin" data-icon="inline-start" />
            Checking
          </Badge>
        ) : readiness.ready ? (
          <Badge variant="success">
            <CircleCheckIcon data-icon="inline-start" />
            Operational
          </Badge>
        ) : (
          <Badge variant="destructive" title="One or more backend dependencies are unavailable.">
            <CircleAlertIcon data-icon="inline-start" />
            Degraded
          </Badge>
        )}
      </div>
    </header>
  );
}
