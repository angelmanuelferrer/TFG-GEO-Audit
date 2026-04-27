import type { RunScorecard } from "@/api/types";
import { Badge } from "@/components/ui/badge";

export function InfoTab({ scorecard }: { scorecard: RunScorecard }) {
  return (
    <div className="bg-card border border-border rounded-lg p-5 space-y-4 max-w-2xl">
      <h3 className="text-sm font-semibold text-foreground">Metadata del Run</h3>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-xs text-muted-foreground">Run ID</p>
          <code className="text-primary font-mono text-xs">{scorecard.run_id}</code>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Timestamp</p>
          <p className="text-foreground">{new Date(scorecard.timestamp).toLocaleString("es-ES")}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Rotation Block</p>
          <p className="text-foreground">{scorecard.rotation_block ?? "Core"}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Queries</p>
          <p className="text-foreground">{scorecard.n_queries} total · {scorecard.n_successful} exitosas</p>
        </div>
      </div>

      {scorecard.n_errors > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-destructive">
            Errores ({scorecard.n_errors})
          </h4>
          <p className="text-xs text-muted-foreground">
            {scorecard.n_errors} queries no pudieron completarse.
          </p>
          {/* List errored queries — those not in per_query_metrics */}
          <div className="flex flex-wrap gap-1.5">
            {scorecard.per_query_metrics
              .filter((m) => !m.is_visible && m.som === 0 && m.total_citations === 0)
              .map((m) => (
                <Badge key={m.query_id} variant="outline" className="text-[10px] border-destructive/40 text-destructive font-mono">
                  {m.query_id}
                </Badge>
              ))}
          </div>
        </div>
      )}

      {/* Derived stats */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-foreground">Avg First Rank por categoría</h4>
        <div className="flex flex-wrap gap-3">
          {Object.entries(scorecard._derived.avg_first_rank_by_category).map(([cat, val]) => (
            <div key={cat} className="bg-surface-elevated rounded-md px-3 py-2">
              <span className="text-[10px] text-muted-foreground capitalize">{cat}</span>
              <p className="text-sm font-semibold text-foreground">{val.toFixed(1)}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <h4 className="text-sm font-medium text-foreground">Avg PAWC por categoría</h4>
        <div className="flex flex-wrap gap-3">
          {Object.entries(scorecard._derived.avg_pawc_by_category).map(([cat, val]) => (
            <div key={cat} className="bg-surface-elevated rounded-md px-3 py-2">
              <span className="text-[10px] text-muted-foreground capitalize">{cat}</span>
              <p className="text-sm font-semibold text-foreground">{val.toFixed(1)}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
