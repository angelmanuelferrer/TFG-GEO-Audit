import { useOverview } from "@/api/hooks";
import { KpiCard } from "@/components/KpiCard";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

const ENGINE_COLORS: Record<string, string> = {
  gemini: "bg-engine-gemini",
  claude: "bg-engine-claude",
  openai: "bg-engine-openai",
};

const ENGINE_TEXT: Record<string, string> = {
  gemini: "text-engine-gemini",
  claude: "text-engine-claude",
  openai: "text-engine-openai",
};

export default function HomePage() {
  const { data, isLoading } = useOverview();

  const exp = data?.experimental;
  const live = data?.live;
  const seo = data?.seo;

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Row 1 — KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Visibilidad Experimental"
          value={exp ? exp.visibility_rate.toFixed(1) : "—"}
          suffix="%"
          delta={exp?.delta_vs_previous?.visibility_rate}
          loading={isLoading}
        />
        <KpiCard
          label="Share of Model"
          value={exp ? exp.avg_som.toFixed(1) : "—"}
          suffix="%"
          delta={exp?.delta_vs_previous?.avg_som}
          loading={isLoading}
        />
        <KpiCard
          label="Engine Coverage (Live)"
          value={live ? live.engine_coverage_avg.toFixed(1) : "—"}
          suffix="%"
          subtitle={live?.latest_run_id}
          loading={isLoading}
        />
        <KpiCard
          label="SEO Mobile Performance"
          value={seo ? seo.mobile.performance.toFixed(0) : "—"}
          subtitle={seo ? `LCP: ${seo.mobile.lcp}` : undefined}
          loading={isLoading}
        />
      </div>

      {/* Row 2 — Two columns */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Left — Latest experimental run */}
        <div className="lg:col-span-3 bg-card border border-border rounded-lg p-5 space-y-4">
          <h2 className="text-sm font-semibold text-foreground">Últimos Runs Experimentales</h2>
          {exp ? (
            <div className="bg-surface-elevated border border-border rounded-md p-4 space-y-3">
              <div className="flex items-center justify-between">
                <code className="text-xs text-primary font-mono">{exp.run_id}</code>
                {exp.rotation_block && (
                  <Badge variant="outline" className="text-xs border-primary/30 text-primary">
                    {exp.rotation_block}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                {new Date(exp.timestamp).toLocaleString("es-ES")}
              </p>
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Queries exitosas</span>
                  <span>{exp.n_successful}/{exp.n_queries}</span>
                </div>
                <Progress value={(exp.n_successful / exp.n_queries) * 100} className="h-2" />
              </div>
              <div className="flex gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground text-xs">Visibility</span>
                  <p className="font-semibold text-foreground">{exp.visibility_rate}%</p>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs">SoM</span>
                  <p className="font-semibold text-foreground">{exp.avg_som}%</p>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs">Citas</span>
                  <p className="font-semibold text-foreground">{exp.avg_citations}</p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Sin datos experimentales</p>
          )}
        </div>

        {/* Right — Live */}
        <div className="lg:col-span-2 bg-card border border-border rounded-lg p-5 space-y-4">
          <h2 className="text-sm font-semibold text-foreground">Live Más Reciente</h2>
          {live ? (
            <>
              <div className="flex items-center justify-between">
                <code className="text-xs text-primary font-mono">{live.latest_run_id}</code>
                <span className="text-xs text-muted-foreground">
                  {new Date(live.timestamp).toLocaleDateString("es-ES")}
                </span>
              </div>
              <p className="text-4xl font-bold text-foreground">
                {live.engine_coverage_avg.toFixed(1)}
                <span className="text-lg text-muted-foreground">%</span>
              </p>
              <div className="space-y-3">
                {Object.entries(live.by_engine).map(([engine, stats]) => (
                  <div key={engine} className="flex items-center gap-3">
                    <div className={cn("w-2 h-2 rounded-full shrink-0", ENGINE_COLORS[engine])} />
                    <span className={cn("text-sm font-medium capitalize w-16", ENGINE_TEXT[engine])}>
                      {engine}
                    </span>
                    <div className="flex-1 text-xs text-muted-foreground text-right">
                      <span className="text-foreground font-medium">{stats.visibility_rate}%</span>
                      {" · SoM "}
                      <span className="text-foreground">{stats.avg_som}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Sin datos live</p>
          )}
        </div>
      </div>

      {/* Row 3 — Alerts */}
      {data?.alerts && data.alerts.length > 0 && (
        <div className="space-y-2">
          {data.alerts.map((alert, i) => (
            <div
              key={i}
              className="bg-warning/10 border border-warning/30 rounded-lg p-3 flex items-center gap-2 text-sm text-warning"
            >
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {alert}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
