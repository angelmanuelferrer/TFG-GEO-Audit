import { useMemo, useState } from "react";
import { useSeoLatest, useSeoHistory } from "@/api/hooks";
import { ScoreGauge } from "@/components/seo/ScoreGauge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { TrendingUp, TrendingDown, Smartphone, Monitor } from "lucide-react";

function parseFecha(f: string) {
  // "2026-02-04_20-07-31" → Date
  const [date, time] = f.split("_");
  const t = time?.replace(/-/g, ":") ?? "00:00:00";
  return new Date(`${date}T${t}`);
}

function formatShort(f: string) {
  const d = parseFecha(f);
  return d.toLocaleDateString("es-ES", { day: "2-digit", month: "short" });
}

function parseMetricValue(s: string): number {
  return parseFloat(s);
}

function lcpColor(s: string) {
  const v = parseMetricValue(s);
  if (v < 2.5) return "text-success";
  if (v <= 4) return "text-warning";
  return "text-destructive";
}

function tbtColor(s: string) {
  const v = parseMetricValue(s);
  if (v < 200) return "text-success";
  if (v <= 600) return "text-warning";
  return "text-destructive";
}

type Range = "week" | "2weeks" | "all";

const tooltipStyle = {
  backgroundColor: "hsl(222 45% 10%)",
  border: "1px solid hsl(213 40% 22%)",
  borderRadius: "8px",
  fontSize: "12px",
};

export default function SeoPage() {
  const { data: latest, isLoading: loadingLatest } = useSeoLatest();
  const { data: history, isLoading: loadingHistory } = useSeoHistory();
  const [range, setRange] = useState<Range>("all");

  const filteredHistory = useMemo(() => {
    if (!history) return [];
    if (range === "all") return history;
    const now = new Date("2026-04-07");
    const days = range === "week" ? 7 : 14;
    const cutoff = new Date(now.getTime() - days * 86400000);
    return history.filter((s) => parseFecha(s.fecha) >= cutoff);
  }, [history, range]);

  const mobileChartData = filteredHistory.map((s) => ({
    fecha: formatShort(s.fecha),
    Performance: s.mobile.performance,
    SEO: s.mobile.seo,
    Accessibility: s.mobile.accessibility,
  }));

  const desktopChartData = filteredHistory.map((s) => ({
    fecha: formatShort(s.fecha),
    Performance: s.desktop.performance,
    SEO: s.desktop.seo,
    Accessibility: s.desktop.accessibility,
  }));

  const webVitalsData = filteredHistory.map((s) => ({
    fecha: formatShort(s.fecha),
    LCP: parseMetricValue(s.mobile.lcp),
    TBT: parseMetricValue(s.mobile.tbt),
  }));

  function trend(key: "performance" | "seo" | "accessibility", device: "mobile" | "desktop") {
    if (filteredHistory.length < 2) return null;
    const first = filteredHistory[0][device][key] as number;
    const last = filteredHistory[filteredHistory.length - 1][device][key] as number;
    return last - first;
  }

  return (
    <div className="space-y-6 max-w-7xl">
      <h1 className="text-xl font-bold text-foreground">SEO Histórico — Lighthouse</h1>

      {/* Gauges */}
      {loadingLatest ? (
        <div className="grid grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-36" />)}
        </div>
      ) : latest ? (
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="grid grid-cols-2 gap-6">
            {/* Mobile */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5"><Smartphone className="h-4 w-4 text-muted-foreground" /> Mobile</h3>
              <div className="flex justify-center gap-6">
                <ScoreGauge value={latest.mobile.performance} label="Performance" />
                <ScoreGauge value={latest.mobile.seo} label="SEO" />
                <ScoreGauge value={latest.mobile.accessibility} label="Accessibility" />
              </div>
              <div className="flex justify-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">LCP:</span>
                  <span className={cn("font-semibold", lcpColor(latest.mobile.lcp))}>{latest.mobile.lcp}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">TBT:</span>
                  <span className={cn("font-semibold", tbtColor(latest.mobile.tbt))}>{latest.mobile.tbt}</span>
                </div>
              </div>
            </div>
            {/* Desktop */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5"><Monitor className="h-4 w-4 text-muted-foreground" /> Desktop</h3>
              <div className="flex justify-center gap-6">
                <ScoreGauge value={latest.desktop.performance} label="Performance" />
                <ScoreGauge value={latest.desktop.seo} label="SEO" />
                <ScoreGauge value={latest.desktop.accessibility} label="Accessibility" />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Sin datos SEO disponibles</p>
      )}

      {/* Range Picker */}
      <div className="flex items-center gap-2">
        {(["week", "2weeks", "all"] as Range[]).map((r) => (
          <Button
            key={r}
            variant={range === r ? "default" : "outline"}
            size="sm"
            onClick={() => setRange(r)}
          >
            {r === "week" ? "Última semana" : r === "2weeks" ? "Últimas 2 sem." : "Todo"}
          </Button>
        ))}
      </div>

      {/* Line Charts */}
      {loadingHistory ? (
        <Skeleton className="h-72" />
      ) : filteredHistory.length === 0 ? (
        <div className="bg-card border border-border rounded-lg p-8 text-center text-muted-foreground text-sm">
          Sin datos de historial SEO disponibles
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Mobile chart */}
          <div className="bg-card border border-border rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5"><Smartphone className="h-4 w-4 text-muted-foreground" /> Mobile — Evolución</h3>
              <div className="flex gap-3 text-xs">
                {(["performance", "seo", "accessibility"] as const).map((k) => {
                  const t = trend(k, "mobile");
                  if (t === null) return null;
                  return (
                    <span key={k} className={cn("flex items-center gap-0.5", t >= 0 ? "text-success" : "text-destructive")}>
                      {t >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                      {Math.abs(t).toFixed(0)}
                    </span>
                  );
                })}
              </div>
            </div>
            <div className="overflow-x-auto chart-scroll">
              <div style={{ minWidth: Math.max(560, mobileChartData.length * 22), height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={mobileChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(213 40% 22%)" />
                    <XAxis dataKey="fecha" tick={{ fill: "hsl(215 20% 65%)", fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: "hsl(215 20% 65%)", fontSize: 11 }} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend iconSize={8} wrapperStyle={{ fontSize: "11px" }} />
                    <Line type="monotone" dataKey="Performance" stroke="hsl(187 94% 43%)" strokeWidth={2} dot={{ r: 3 }} />
                    <Line type="monotone" dataKey="SEO" stroke="hsl(263 70% 66%)" strokeWidth={2} dot={{ r: 3 }} />
                    <Line type="monotone" dataKey="Accessibility" stroke="hsl(160 84% 39%)" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Desktop chart */}
          <div className="bg-card border border-border rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5"><Monitor className="h-4 w-4 text-muted-foreground" /> Desktop — Evolución</h3>
              <div className="flex gap-3 text-xs">
                {(["performance", "seo", "accessibility"] as const).map((k) => {
                  const t = trend(k, "desktop");
                  if (t === null) return null;
                  return (
                    <span key={k} className={cn("flex items-center gap-0.5", t >= 0 ? "text-success" : "text-destructive")}>
                      {t >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                      {Math.abs(t).toFixed(0)}
                    </span>
                  );
                })}
              </div>
            </div>
            <div className="overflow-x-auto chart-scroll">
              <div style={{ minWidth: Math.max(560, desktopChartData.length * 22), height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={desktopChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(213 40% 22%)" />
                    <XAxis dataKey="fecha" tick={{ fill: "hsl(215 20% 65%)", fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: "hsl(215 20% 65%)", fontSize: 11 }} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend iconSize={8} wrapperStyle={{ fontSize: "11px" }} />
                    <Line type="monotone" dataKey="Performance" stroke="hsl(187 94% 43%)" strokeWidth={2} dot={{ r: 3 }} />
                    <Line type="monotone" dataKey="SEO" stroke="hsl(263 70% 66%)" strokeWidth={2} dot={{ r: 3 }} />
                    <Line type="monotone" dataKey="Accessibility" stroke="hsl(160 84% 39%)" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Web Vitals chart */}
      {webVitalsData.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5"><Smartphone className="h-4 w-4 text-muted-foreground" /> Mobile — Web Vitals (LCP & TBT)</h3>
          <div className="overflow-x-auto chart-scroll">
            <div style={{ minWidth: Math.max(560, webVitalsData.length * 22), height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={webVitalsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(213 40% 22%)" />
                  <XAxis dataKey="fecha" tick={{ fill: "hsl(215 20% 65%)", fontSize: 11 }} />
                  <YAxis yAxisId="lcp" tick={{ fill: "hsl(215 20% 65%)", fontSize: 11 }} label={{ value: "s", position: "insideLeft", style: { fill: "hsl(215 20% 65%)", fontSize: 10 } }} />
                  <YAxis yAxisId="tbt" orientation="right" tick={{ fill: "hsl(215 20% 65%)", fontSize: 11 }} label={{ value: "ms", position: "insideRight", style: { fill: "hsl(215 20% 65%)", fontSize: 10 } }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend iconSize={8} wrapperStyle={{ fontSize: "11px" }} />
                  <Line yAxisId="lcp" type="monotone" dataKey="LCP" stroke="hsl(0 84% 60%)" strokeWidth={2} dot={{ r: 3 }} />
                  <Line yAxisId="tbt" type="monotone" dataKey="TBT" stroke="hsl(38 92% 50%)" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
