import type { RunScorecard } from "@/api/types";
import { cn } from "@/lib/utils";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const CATEGORY_COLORS: Record<string, string> = {
  comparativa: "hsl(var(--secondary))",
  informacional: "hsl(var(--primary))",
  navegacional: "hsl(var(--success))",
};

function visibilityColor(rate: number) {
  if (rate >= 85) return "text-success";
  if (rate >= 70) return "text-warning";
  return "text-destructive";
}

function MetricRow({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="text-right">
        <span className="text-sm font-semibold text-foreground">{value}</span>
        {note && <span className="text-[10px] text-muted-foreground ml-1">{note}</span>}
      </div>
    </div>
  );
}

export function CategoryTab({ scorecard }: { scorecard: RunScorecard }) {
  const categories = Object.entries(scorecard.by_category);
  const { avg_first_rank_by_category, avg_pawc_by_category } = scorecard._derived;

  const chartData = categories.map(([name, stats]) => ({
    name,
    value: stats.visibility_rate,
  }));

  return (
    <div className="space-y-4">
      {/* Category cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {categories.map(([name, stats]) => {
          const avgRank = avg_first_rank_by_category[name];
          const avgPawc = avg_pawc_by_category[name];

          return (
            <div key={name} className="bg-card border border-border rounded-lg p-4 space-y-1">
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: CATEGORY_COLORS[name] || "hsl(var(--muted))" }}
                  />
                  <span className="text-sm font-semibold capitalize">{name}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {stats.n_successful}/{stats.n} queries
                  {stats.n_errors > 0 && (
                    <span className="text-destructive ml-1">({stats.n_errors} err)</span>
                  )}
                </span>
              </div>

              {/* Visibility con barra */}
              <div className="pb-2 mb-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-muted-foreground">Visibility Rate</span>
                  <span className={cn("text-sm font-semibold", visibilityColor(stats.visibility_rate))}>
                    {stats.visibility_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{ width: `${stats.visibility_rate}%` }}
                  />
                </div>
              </div>

              <MetricRow
                label="Avg SoM"
                value={`${stats.avg_som.toFixed(1)}%`}
                note="share of mind"
              />
              <MetricRow
                label="Avg Citations"
                value={stats.avg_citations.toFixed(1)}
                note="por query"
              />
              <MetricRow
                label="Avg First Rank"
                value={avgRank != null ? `#${avgRank.toFixed(1)}` : "—"}
                note="posición 1ª cita"
              />
              <MetricRow
                label="Avg PAWC"
                value={avgPawc != null ? avgPawc.toFixed(1) : "—"}
                note="pos-adj words"
              />
            </div>
          );
        })}
      </div>

      {/* Donut chart */}
      <div className="bg-card border border-border rounded-lg p-4 flex flex-col items-center">
        <p className="text-xs text-muted-foreground font-medium mb-3">Visibility Rate por categoría</p>
        <ResponsiveContainer width="100%" height={160}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
            >
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={CATEGORY_COLORS[entry.name] || "hsl(var(--muted))"} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(222 45% 10%)",
                border: "1px solid hsl(213 40% 22%)",
                borderRadius: "8px",
                fontSize: "12px",
              }}
              labelStyle={{ color: "hsl(210 40% 96%)" }}
              itemStyle={{ color: "hsl(210 40% 96%)" }}
              formatter={(value: number, _name: string, props) => [
                `${value.toFixed(1)}%`,
                props.payload?.name ?? "Visibility",
              ]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex gap-4 mt-1">
          {categories.map(([name]) => (
            <div key={name} className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: CATEGORY_COLORS[name] }}
              />
              <span className="text-[10px] text-muted-foreground capitalize">{name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
