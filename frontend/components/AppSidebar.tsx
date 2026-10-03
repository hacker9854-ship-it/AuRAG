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
  ZapIcon,
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

const machineMoneyItems = [
  { label: "Command Center", icon: LayoutDashboardIcon, href: "/" },
  { label: "Machine Money", icon: ZapIcon, href: "/machine-money", highlight: true },
  { label: "Predictive Watch", icon: GaugeIcon, href: "/predictive-watch" },
];

const evidenceRagItems = [
  { label: "Investigate", icon: SearchIcon, href: "/investigate" },
  { label: "Work Orders", icon: ClipboardListIcon, href: "/work-orders" },
  { label: "Operations & Governance", icon: SlidersIcon, href: "/operations" },
  { label: "Knowledge Risk", icon: UserRoundSearchIcon, href: "/knowledge-risk" },
  { label: "RAG Comparison", icon: GitCompareArrowsIcon, href: "/comparison" },
  { label: "Evaluation", icon: ChartNoAxesCombinedIcon, href: "/evaluation" },
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
              tooltip="AuRAG Autonomous Machine Money"
              render={<Link href="/" onClick={closeMobileSidebar} />}
            >
              <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-amber-500 font-heading font-bold text-slate-950">
                ⚡
              </div>
              <div className="flex min-w-0 flex-col items-start group-data-[collapsible=icon]:hidden">
                <span className="font-heading text-base font-semibold tracking-tight">AuRAG</span>
                <span className="truncate text-xs text-muted-foreground">Autonomous Machine Money · by Niss</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        {/* Machine Money Flagship Group */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[11px] font-semibold text-amber-500/90 uppercase tracking-wider">
            Autonomous Machine Money
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {machineMoneyItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(`${item.href}/`));
                return (
                  <SidebarMenuItem key={item.label}>
                    <SidebarMenuButton
                      isActive={isActive}
                      tooltip={item.label}
                      className={item.highlight ? "font-semibold text-amber-500 hover:text-amber-400" : ""}
                      render={<Link href={item.href} onClick={closeMobileSidebar} />}
                    >
                      <Icon className={item.highlight ? "text-amber-500" : undefined} />
                      <span className="flex-1">{item.label}</span>
                      {item.highlight && (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 group-data-[collapsible=icon]:hidden">
                          Lightning
                        </span>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Evidence & Justification (GraphRAG) Group */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Evidence & Justification (RAG)
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {evidenceRagItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(`${item.href}/`));
                return (
                  <SidebarMenuItem key={item.label}>
                    <SidebarMenuButton
                      isActive={isActive}
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
        <div className="flex items-center justify-between px-2.5 pt-2 pb-1 text-[10px] text-muted-foreground/80 group-data-[collapsible=icon]:hidden font-mono border-t border-border/40">
          <span>AuRAG by Niss</span>
          <span className="text-amber-500 font-semibold">BOSS 2026</span>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
