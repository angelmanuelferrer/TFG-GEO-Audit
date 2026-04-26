import { useParams } from "react-router-dom";
import { useRunScorecard, useRunRaw } from "@/api/hooks";
import { KpiCard } from "@/components/KpiCard";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { CategoryTab } from "@/components/experimental/CategoryTab";
import { PerQueryTab } from "@/components/experimental/PerQueryTab";
import { RawTab } from "@/components/experimental/RawTab";
import { InfoTab } from "@/components/experimental/InfoTab";

function formatDate(ts: string) {
  const d = new Date(ts);
  return d.toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" }) +
    ", " + d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
}

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const { data: scorecard, isLoading } = useRunScorecard(runId);
  const { data: rawData } = useRunRaw(runId);

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-7xl">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      </div>
    );
  }

  if (!scorecard) {
    return <div className="text-muted-foreground">Run no encontrado</div>;
  }

  // Compute avg first rank across all categories
  const rankValues = Object.values(scorecard._derived.avg_first_rank_by_category);
  const avgFirstRank = rankValues.length > 0
    ? (rankValues.reduce((a, b) => a + b, 0) / rankValues.length)
    : null;

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3">
        <code className="text-lg font-mono font-bold text-primary">{scorecard.run_id}</code>
        {scorecard.rotation_block && (
          <Badge variant="outline" className="border-primary/40 text-primary">
            {scorecard.rotation_block}
          </Badge>
        )}
        <span className="text-sm text-muted-foreground">{formatDate(scorecard.timestamp)}</span>
        <span className="text-sm text-muted-foreground ml-auto">
          {scorecard.n_successful}/{scorecard.n_queries} queries exitosas
        </span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Visibility Rate" value={scorecard.visibility_rate.toFixed(1)} suffix="%" />
        <KpiCard label="Avg SoM" value={scorecard.avg_som.toFixed(1)} suffix="%" />
        <KpiCard label="Avg Citations" value={scorecard.avg_citations.toFixed(2)} />
        <KpiCard label="Avg First Rank" value={avgFirstRank ? avgFirstRank.toFixed(1) : "—"} />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="category" className="space-y-4">
        <TabsList className="bg-surface-elevated border border-border">
          <TabsTrigger value="category">Por Categoría</TabsTrigger>
          <TabsTrigger value="queries">Por Query</TabsTrigger>
          <TabsTrigger value="raw">Raw</TabsTrigger>
          <TabsTrigger value="info">Info</TabsTrigger>
        </TabsList>

        <TabsContent value="category">
          <CategoryTab scorecard={scorecard} />
        </TabsContent>
        <TabsContent value="queries">
          <PerQueryTab metrics={scorecard.per_query_metrics} />
        </TabsContent>
        <TabsContent value="raw">
          <RawTab data={rawData} perQueryMetrics={scorecard.per_query_metrics} />
        </TabsContent>
        <TabsContent value="info">
          <InfoTab scorecard={scorecard} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
