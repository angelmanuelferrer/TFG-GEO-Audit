import { useState } from "react";
import { useExperimentalRuns, useCompareRuns } from "@/api/hooks";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { KpiCard } from "@/components/KpiCard";
import { cn } from "@/lib/utils";
import { GitCompare, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function ComparePage() {
  const { data: runsList } = useExperimentalRuns();
  const [runA, setRunA] = useState("");
  const [runB, setRunB] = useState("");
  const [triggered, setTriggered] = useState(false);

  const canCompare = runA && runB && runA !== runB;
  const { data, isLoading } = useCompareRuns(runA, runB, triggered && canCompare);

  const handleCompare = () => {
    if (canCompare) setTriggered(true);
  };

  const runs = runsList?.items ?? [];

  const runAMeta = runs.find((r) => r.run_id === runA);
  const runBMeta = runs.find((r) => r.run_id === runB);
  const differentBlocks =
    runA && runB && runAMeta && runBMeta && runAMeta.rotation_block !== runBMeta.rotation_block;

  // Sort som_shifts by abs delta descending, take top 10
  const chartData = data
    ? [...data.som_shifts]
        .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
        .slice(0, 10)
        .map((s) => ({ name: s.query_id, delta: s.delta }))
    : [];

  return (
    <div className="space-y-6 max-w-7xl">
      <h1 className="text-xl font-bold text-foreground">Comparar Runs</h1>

      {/* Selectors */}
      <div className="flex flex-wrap items-end gap-4">
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground font-medium">Run A (anterior)</label>
          <Select value={runA} onValueChange={(v) => { setRunA(v); setTriggered(false); }}>
            <SelectTrigger className="w-64 bg-surface-elevated border-border">
              <SelectValue placeholder="Selecciona run A" />
            </SelectTrigger>
            <SelectContent>
              {runs.map((r) => (
                <SelectItem key={r.run_id} value={r.run_id}>
                  {r.run_id}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground font-medium">Run B (nuevo)</label>
          <Select value={runB} onValueChange={(v) => { setRunB(v); setTriggered(false); }}>
            <SelectTrigger className="w-64 bg-surface-elevated border-border">
              <SelectValue placeholder="Selecciona run B" />
            </SelectTrigger>
            <SelectContent>
              {runs.map((r) => (
                <SelectItem key={r.run_id} value={r.run_id}>
                  {r.run_id}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button onClick={handleCompare} disabled={!canCompare} className="gap-1.5">
          <GitCompare className="h-4 w-4" />
          Comparar
        </Button>
      </div>

      {differentBlocks && (
        <div className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 px-4 py-3 text-sm text-warning">
          <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
          <span>
            Los runs tienen bloques de rotación distintos (<span className="font-mono">{runAMeta?.rotation_block ?? "Core"}</span> vs <span className="font-mono">{runBMeta?.rotation_block ?? "Core"}</span>). Las queries no son las mismas, por lo que las métricas comparadas no son directamente equivalentes.
          </span>
        </div>
      )}

      {isLoading && (
        <div className="text-muted-foreground text-sm py-8 text-center">Cargando comparación...</div>
      )}

      {data && (
        <div className="space-y-6">
          {/* Delta Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <KpiCard label="Δ Visibility Rate" value={data.deltas.visibility_rate.toFixed(2)} suffix="pp" delta={data.deltas.visibility_rate} />
            <KpiCard label="Δ Avg SoM" value={data.deltas.avg_som.toFixed(2)} suffix="pp" delta={data.deltas.avg_som} />
            <KpiCard label="Δ Avg Citations" value={data.deltas.avg_citations.toFixed(2)} delta={data.deltas.avg_citations} />
          </div>

          {/* Gained / Lost */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-card border border-border rounded-lg p-4 space-y-2">
              <h3 className="text-sm font-semibold text-success flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4" />
                Queries Ganadas ({data.queries_gained.length})
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {data.queries_gained.length === 0 ? (
                  <span className="text-xs text-muted-foreground">Ninguna</span>
                ) : (
                  data.queries_gained.map((q) => (
                    <Badge key={q} className="bg-success/10 text-success border-success/30 font-mono text-xs">
                      {q}
                    </Badge>
                  ))
                )}
              </div>
            </div>
            <div className="bg-card border border-border rounded-lg p-4 space-y-2">
              <h3 className="text-sm font-semibold text-destructive flex items-center gap-1.5">
                <TrendingDown className="h-4 w-4" />
                Queries Perdidas ({data.queries_lost.length})
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {data.queries_lost.length === 0 ? (
                  <span className="text-xs text-muted-foreground">Ninguna</span>
                ) : (
                  data.queries_lost.map((q) => (
                    <Badge key={q} className="bg-destructive/10 text-destructive border-destructive/30 font-mono text-xs">
                      {q}
                    </Badge>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* SoM Shifts Table */}
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-border">
              <h3 className="text-sm font-semibold text-foreground">SoM Shifts</h3>
            </div>
            <div className="grid grid-cols-[80px_1fr_1fr_1fr] gap-2 px-4 py-2 border-b border-border text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
              <span>Query</span>
              <span>Run A</span>
              <span>Run B</span>
              <span>Delta</span>
            </div>
            {data.som_shifts.map((s) => (
              <div key={s.query_id} className="grid grid-cols-[80px_1fr_1fr_1fr] gap-2 px-4 py-2.5 border-b border-border last:border-0 items-center hover:bg-surface-elevated transition-colors">
                <Badge variant="outline" className="font-mono text-[10px] w-fit">{s.query_id}</Badge>
                <span className="text-sm text-muted-foreground">{s.from_som.toFixed(1)}%</span>
                <span className="text-sm text-foreground">{s.to_som.toFixed(1)}%</span>
                <span className={cn("text-sm font-semibold", s.delta >= 0 ? "text-success" : "text-destructive")}>
                  {s.delta >= 0 ? "+" : ""}{s.delta.toFixed(1)}
                </span>
              </div>
            ))}
          </div>

          {/* Bar Chart */}
          {chartData.length > 0 && !differentBlocks && (
            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-foreground mb-4">Top cambios de SoM</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(213 40% 22%)" />
                  <XAxis type="number" tick={{ fill: "hsl(215 20% 65%)", fontSize: 11 }} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={60}
                    tick={{ fill: "hsl(215 20% 65%)", fontSize: 11, fontFamily: "monospace" }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "hsl(222 45% 10%)", border: "1px solid hsl(213 40% 22%)", borderRadius: "8px", fontSize: "12px", color: "hsl(215 20% 85%)" }}
                    labelStyle={{ color: "hsl(215 20% 85%)" }}
                    itemStyle={{ color: "hsl(215 20% 85%)" }}
                    formatter={(value: number) => [`${value.toFixed(1)}pp`, "Δ SoM"]}
                  />
                  <Bar dataKey="delta" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, idx) => (
                      <Cell
                        key={idx}
                        fill={entry.delta >= 0 ? "hsl(160 84% 39%)" : "hsl(0 84% 60%)"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
