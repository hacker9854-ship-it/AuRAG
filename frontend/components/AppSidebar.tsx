"use client";

import {
  ChartNoAxesCombinedIcon,
  ClipboardListIcon,
  GitCompareArrowsIcon,
  GaugeIcon,
  LayoutDashboardIcon,
  SearchIcon,
  SlidersIcon,
  UserRoundSearchIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarSeparator,
  useSidebar,
} from "@/components/ui/sidebar";
import type { ReadinessResponse } from "@/lib/api";

const workspaceItems = [
  { label: "Command Center", icon: LayoutDashboardIcon, href: "/" },
  { label: "Investigate", icon: SearchIcon, href: "/investigate" },
  { label: "Predictive Watch", icon: GaugeIcon, href: "/predictive-watch" },
  { label: "Operations & Governance", icon: SlidersIcon, href: "/operations" },
  { label: "Knowledge Risk", icon: UserRoundSearchIcon, href: "/knowledge-risk" },
  { label: "RAG Comparison", icon: GitCompareArrowsIcon, href: "/comparison" },
  { label: "Evaluation", icon: ChartNoAxesCombinedIcon, href: "/evaluation" },
  { label: "Work Orders", icon: ClipboardListIcon, href: "/work-orders" },
];

export default function AppSidebar({ readiness }: { readiness: ReadinessResponse | null }) {
  const { isMobile, setOpenMobile } = useSidebar();
  const pathname = usePathname();

  function closeMobileSidebar() {
    if (isMobile) setOpenMobile(false);
  }

  return (
    <Sidebar collapsible="icon" variant="sidebar">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              tooltip="AuRAG Command Center"
              render={<Link href="/" onClick={closeMobileSidebar} />}
            >
              <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary font-heading font-semibold text-primary-foreground">
                A
              </div>
              <div className="flex min-w-0 flex-col items-start group-data-[collapsible=icon]:hidden">
                <span className="font-heading text-base font-semibold tracking-tight">AuRAG</span>
                <span className="truncate text-xs text-muted-foreground">Operations intelligence</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {workspaceItems.map((item) => {
                const Icon = item.icon;
                return (
                  <SidebarMenuItem key={item.label}>
                    <SidebarMenuButton
                      isActive={
                        pathname === item.href ||
                        (item.href !== "/" && pathname.startsWith(`${item.href}/`))
                      }
                      tooltip={item.label}
                      render={<Link href={item.href} onClick={closeMobileSidebar} />}
                    >
                      <Icon />
                      <span>{item.label}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarSeparator />
        <div className="flex items-center gap-2 px-2 py-1.5 group-data-[collapsible=icon]:justify-center">
          <span
            className={
              readiness?.ready
                ? "size-2 shrink-0 rounded-full bg-success shadow-[0_0_0_3px_color-mix(in_oklch,var(--success)_14%,transparent)]"
                : readiness === null
                  ? "size-2 shrink-0 rounded-full bg-warning"
                  : "size-2 shrink-0 rounded-full bg-destructive"
            }
          />
          <div className="min-w-0 group-data-[collapsible=icon]:hidden">
            <div className="text-xs font-medium">
              {readiness === null
                ? "Checking systems"
                : readiness.ready
                  ? "Systems operational"
                  : "Systems degraded"}
            </div>
            <div className="text-xs text-muted-foreground">
              {readiness?.ready ? "Dependencies ready" : "Open health status for details"}
            </div>
          </div>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
