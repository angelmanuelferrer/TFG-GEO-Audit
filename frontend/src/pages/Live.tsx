import { useState } from "react";
import { useLiveRunsList, useLiveRun, useCoverageMatrix, useSentimentDistribution } from "@/api/hooks";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { EngineCards } from "@/components/live/EngineCards";
import { CoverageHeatmap } from "@/components/live/CoverageHeatmap";
import { SentimentDonuts } from "@/components/live/SentimentDonuts";
import { LiveQueryTable } from "@/components/live/LiveQueryTable";
import { KpiCard } from "@/components/KpiCard";

export default function LivePage() {
  const { data: runsList } = useLiveRunsList();
  const [selectedRun, setSelectedRun] = useState("latest");

  const { data: liveRun, isLoading } = useLiveRun(selectedRun);
  const runId = liveRun?.run_id ?? selectedRun;
  const { data: matrix } = useCoverageMatrix(runId);
  const { data: sentiment } = useSentimentDistribution(runId);

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <h1 className="text-xl font-bold text-foreground">Live Multi-motor</h1>
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground">Semana:</label>
          <Select value={selectedRun} onValueChange={setSelectedRun}>
            <SelectTrigger className="w-52 bg-surface-elevated border-border">
              <SelectValue placeholder="Selecciona semana" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="latest">Más reciente</SelectItem>
              {runsList?.items.map((r) => (
                <SelectItem key={r.run_id} value={r.run_id}>
                  {r.run_id}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-32" />)}
          </div>
          <Skeleton className="h-48" />
        </div>
      ) : liveRun ? (
        <>
          {/* Engine Cards + Global KPI */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-1">
              <KpiCard
                label="Engine Coverage Avg"
                value={liveRun.engine_coverage_avg.toFixed(1)}
                suffix="%"
                subtitle={`${liveRun.n_queries} queries · ${liveRun.engines.length} motores`}
              />
            </div>
            <div className="md:col-span-3">
              <EngineCards engines={liveRun.engines} summary={liveRun.summary} />
            </div>
          </div>

          {/* Heatmap */}
          {matrix && <CoverageHeatmap matrix={matrix} />}

          {/* Sentiment */}
          {sentiment && sentiment.length > 0 && <SentimentDonuts data={sentiment} />}

          {/* Query Table */}
          <LiveQueryTable results={liveRun.results} engines={liveRun.engines} />
        </>
      ) : (
        <div className="text-muted-foreground text-sm py-8 text-center">No hay datos live disponibles</div>
      )}
    </div>
  );
}
