"use client";

import { useEffect, useState } from "react";
import { NetworkIcon, SearchIcon } from "lucide-react";
import * as ResizablePrimitive from "react-resizable-panels";
import ChatPanel from "@/components/ChatPanel";
import GraphPanel from "@/components/GraphPanel";
import type { ChatResponse } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type InvestigationView = "investigation" | "evidence";

function WorkspaceCard({
  title,
  description,
  status,
  statusVariant = "outline",
  children,
}: {
  title: string;
  description: string;
  status: string;
  statusVariant?: "outline" | "success" | "info";
  children: React.ReactNode;
}) {
  return (
    <Card className="h-full min-h-0 gap-0 py-0">
      <CardHeader className="shrink-0 border-b py-4">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
        <CardAction>
          <Badge variant={statusVariant}>{status}</Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="min-h-0 flex-1 p-0">{children}</CardContent>
    </Card>
  );
}

function useDesktopWorkspace() {
  const [desktop, setDesktop] = useState<boolean | null>(null);

  useEffect(() => {
    const query = window.matchMedia("(min-width: 1024px)");
    const update = () => setDesktop(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return desktop;
}

export default function InvestigatePage() {
  const [selected, setSelected] = useState<ChatResponse | null>(null);
  const [mobileView, setMobileView] = useState<InvestigationView>("investigation");
  const desktop = useDesktopWorkspace();

  function handleScoreUpdate(response: ChatResponse) {
    setSelected((current) => (current?.score_id === response.score_id ? response : current));
  }

  function selectAndReveal(response: ChatResponse) {
    setSelected(response);
    setMobileView("evidence");
  }

  const investigation = (
    <WorkspaceCard
      title="Investigation"
      description="Ask a question and review the routed operational answer."
      status="Agent ready"
      statusVariant="success"
    >
      <ChatPanel
        selectedScoreId={selected?.score_id ?? null}
        onSelectMessage={setSelected}
        onSelectFromCitation={selectAndReveal}
        onScoreUpdate={handleScoreUpdate}
      />
    </WorkspaceCard>
  );

  const evidence = (
    <WorkspaceCard
      title="Answer evidence"
      description="The graph trail for the currently selected answer."
      status={selected ? "Answer selected" : "No answer selected"}
      statusVariant={selected ? "info" : "outline"}
    >
      <GraphPanel graphPaths={selected?.graph_paths ?? null} query={selected?.user_query ?? null} />
    </WorkspaceCard>
  );

  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-4 p-4 sm:p-6">
        <section className="flex flex-col gap-1">
          <h1 className="font-heading text-xl font-semibold tracking-tight sm:text-2xl">Operational investigation</h1>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Ask one operational question, evaluate the answer, and inspect its evidence in the same working context.
          </p>
        </section>

        {desktop === null ? (
          <Skeleton className="h-[min(76vh,780px)] min-h-[600px] w-full rounded-xl" />
        ) : desktop ? (
          <div className="h-[min(76vh,780px)] min-h-[600px]">
            <ResizablePrimitive.Group
              data-slot="resizable-panel-group"
              className="flex h-full w-full"
              orientation="horizontal"
            >
              <ResizablePrimitive.Panel data-slot="resizable-panel" defaultSize={48} minSize={34}>
                <div className="h-full pr-2">{investigation}</div>
              </ResizablePrimitive.Panel>
              <ResizablePrimitive.Separator
                data-slot="resizable-handle"
                className="relative flex w-px items-center justify-center bg-border ring-offset-background after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 focus-visible:ring-1 focus-visible:ring-ring focus-visible:outline-hidden"
              >
                <div className="z-10 flex h-6 w-1 shrink-0 rounded-lg bg-border" />
              </ResizablePrimitive.Separator>
              <ResizablePrimitive.Panel data-slot="resizable-panel" defaultSize={52} minSize={38}>
                <div className="h-full pl-2">{evidence}</div>
              </ResizablePrimitive.Panel>
            </ResizablePrimitive.Group>
          </div>
        ) : (
          <Tabs
            value={mobileView}
            onValueChange={(value) => setMobileView(value as InvestigationView)}
            className="min-h-0"
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="investigation">
                <SearchIcon data-icon="inline-start" />
                Investigation
              </TabsTrigger>
              <TabsTrigger value="evidence">
                <NetworkIcon data-icon="inline-start" />
                Evidence
              </TabsTrigger>
            </TabsList>
            <TabsContent value="investigation" keepMounted className="h-[max(600px,72svh)]">
              {investigation}
            </TabsContent>
            <TabsContent value="evidence" keepMounted className="h-[max(600px,72svh)]">
              {evidence}
            </TabsContent>
          </Tabs>
        )}
    </div>
  );
}
