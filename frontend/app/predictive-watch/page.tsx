import TelemetryPanel from "@/components/TelemetryPanel";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function PredictiveWatchPage() {
  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-4 p-4 sm:p-6">
        <section className="flex flex-col gap-1">
          <h1 className="font-heading text-xl font-semibold tracking-tight sm:text-2xl">Predictive watch</h1>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Compare simulated sensor drift with known failure signatures and prepare a reviewable intervention.
          </p>
        </section>

        <Card className="min-h-[720px] gap-0 py-0">
          <CardHeader className="border-b py-4">
            <CardTitle>Failure signature simulation</CardTitle>
            <CardDescription>
              Live and simulated signals create durable warnings and human-reviewed work orders.
            </CardDescription>
            <CardAction>
              <Badge variant="warning">Simulation</Badge>
            </CardAction>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 p-0">
            <TelemetryPanel />
          </CardContent>
        </Card>
    </div>
  );
}
