import {
  BookOpenCheckIcon,
  BriefcaseBusinessIcon,
  ShieldAlertIcon,
  UserRoundSearchIcon,
  WrenchIcon,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
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
import type { KnowledgeRiskResponse, PersonKnowledgeRisk } from "@/lib/api";

const severityVariant = {
  critical: "destructive",
  elevated: "warning",
  monitored: "outline",
} as const;

function SummaryCard({
  label,
  value,
  detail,
  icon: Icon,
}: {
  label: string;
  value: number;
  detail: string;
  icon: typeof UserRoundSearchIcon;
}) {
  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="text-muted-foreground">{label}</CardTitle>
        <CardAction>
          <Icon />
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="data-mono text-2xl font-semibold tracking-tight">{value}</div>
        <p className="mt-1 text-xs leading-5 text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  );
}

function EvidenceBadges({
  label,
  values,
}: {
  label: string;
  values: string[];
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</div>
      <div className="flex flex-wrap gap-1.5">
        {values.length ? (
          values.map((value) => (
            <Badge key={value} variant="outline">
              {value}
            </Badge>
          ))
        ) : (
          <span className="text-sm text-muted-foreground">No linked records</span>
        )}
      </div>
    </div>
  );
}

function PersonRiskCard({ person }: { person: PersonKnowledgeRisk }) {
  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle>{person.name}</CardTitle>
        <CardDescription>
          {person.role} · {person.department}
        </CardDescription>
        <CardAction className="flex items-center gap-2">
          <Badge variant={severityVariant[person.severity]}>{person.severity}</Badge>
          <div className="data-mono text-2xl font-semibold">{person.risk_score}</div>
        </CardAction>
      </CardHeader>
      <CardContent className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
        <div className="flex flex-col gap-3 rounded-lg bg-muted/45 p-4">
          <div>
            <div className="text-xs text-muted-foreground">Retirement horizon</div>
            <div className="mt-1 font-heading text-xl font-medium">
              {person.years_to_retirement} {person.years_to_retirement === 1 ? "year" : "years"}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Knowledge coverage</div>
            <div className="mt-1 font-heading text-xl font-medium">
              {person.knowledge_coverage.coverage_pct}% covered
            </div>
          </div>
          <div className="text-xs leading-5 text-muted-foreground">
            {person.knowledge_coverage.uncovered_assets} uncovered of {person.equipment.length} linked assets
          </div>
        </div>

        <div className="grid gap-5">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <EvidenceBadges label="Equipment" values={person.equipment} />
            <EvidenceBadges label="Failure events" values={person.failure_events} />
            <EvidenceBadges label="Work orders" values={person.work_orders} />
            <EvidenceBadges label="Documents" values={person.documents} />
          </div>

          <div className="flex flex-col gap-2">
            <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Recommended actions
            </div>
            {person.recommended_actions.map((action, index) => (
              <div key={`${action.type}-${index}`} className="rounded-lg border bg-background p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={action.priority === "critical" ? "destructive" : "warning"}>
                    {action.type.replaceAll("_", " ")}
                  </Badge>
                  {action.equipment?.map((tag) => (
                    <Badge key={tag} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{action.description}</p>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function KnowledgeRiskView({ data }: { data: KnowledgeRiskResponse }) {
  if (!data.people.length) {
    return (
      <Card>
        <CardContent>
          <Empty>
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <BookOpenCheckIcon />
              </EmptyMedia>
              <EmptyTitle>No retirement risk in this horizon</EmptyTitle>
              <EmptyDescription>
                Expand the horizon or ingest additional personnel and work-order records.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Knowledge risk summary">
        <SummaryCard
          label="People at risk"
          value={data.summary.people_at_risk}
          detail={`Within ${data.retirement_horizon} years`}
          icon={UserRoundSearchIcon}
        />
        <SummaryCard
          label="Critical profiles"
          value={data.summary.critical}
          detail="Immediate capture priority"
          icon={ShieldAlertIcon}
        />
        <SummaryCard
          label="Elevated profiles"
          value={data.summary.elevated}
          detail="Planned transfer required"
          icon={BriefcaseBusinessIcon}
        />
        <SummaryCard
          label="Uncovered assets"
          value={data.summary.uncovered_assets}
          detail="No identified successor coverage"
          icon={WrenchIcon}
        />
      </section>

      <section className="flex flex-col gap-4" aria-label="Ranked personnel risk">
        {data.people.map((person) => (
          <PersonRiskCard key={person.person_id} person={person} />
        ))}
      </section>
    </div>
  );
}

