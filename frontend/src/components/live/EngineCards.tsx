import type { LiveEngineSummary } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const ENGINE_META: Record<string, { color: string; borderColor: string; tier: string }> = {
  gemini: { color: "text-engine-gemini", borderColor: "border-l-[hsl(var(--engine-gemini))]", tier: "full" },
  claude: { color: "text-engine-claude", borderColor: "border-l-[hsl(var(--engine-claude))]", tier: "light" },
  openai: { color: "text-engine-openai", borderColor: "border-l-[hsl(var(--engine-openai))]", tier: "medium" },
};

function visibilityColor(rate: number) {
  if (rate >= 40) return "text-success";
  if (rate >= 20) return "text-warning";
  return "text-destructive";
}

interface EngineCardsProps {
  engines: string[];
  summary: Record<string, LiveEngineSummary>;
}

export function EngineCards({ engines, summary }: EngineCardsProps) {
  return (
    <div className={cn("grid gap-4", engines.length === 1 ? "grid-cols-1" : engines.length === 2 ? "grid-cols-2" : "grid-cols-3")}>
      {engines.map((engine) => {
        const stats = summary[engine];
        if (!stats) return null;
        const meta = ENGINE_META[engine] ?? { color: "text-foreground", borderColor: "border-l-border", tier: "—" };

        return (
          <div
            key={engine}
            className={cn(
              "bg-card border border-border rounded-lg p-4 border-l-4 space-y-2",
              meta.borderColor
            )}
          >
            <div className="flex items-center justify-between">
              <span className={cn("text-sm font-semibold capitalize", meta.color)}>{engine}</span>
              <Badge variant="outline" className="text-[10px] text-muted-foreground">
                {meta.tier}
              </Badge>
            </div>
            <p className={cn("text-3xl font-bold", visibilityColor(stats.visibility_rate))}>
              {stats.visibility_rate.toFixed(1)}
              <span className="text-base text-muted-foreground ml-0.5">%</span>
            </p>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <p className="text-muted-foreground">SoM</p>
                <p className="text-foreground font-medium">{stats.avg_som.toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">Queries</p>
                <p className="text-foreground font-medium">{stats.n_queries}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Visibles</p>
                <p className="text-foreground font-medium">{stats.n_visible}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
