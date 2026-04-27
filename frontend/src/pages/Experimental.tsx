import { useExperimentalRuns } from "@/api/hooks";
import { useNavigate } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { GitCompare, Eye, Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { toast } from "sonner";

function formatDate(ts: string) {
  const d = new Date(ts);
  return d.toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" }) +
    ", " + d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
}

function visibilityColor(rate: number) {
  if (rate >= 85) return "text-success";
  if (rate >= 70) return "text-warning";
  return "text-destructive";
}

function progressColor(pct: number) {
  if (pct >= 90) return "bg-success";
  if (pct >= 70) return "bg-warning";
  return "bg-destructive";
}

function CopyableId({ id }: { id: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(id);
    setCopied(true);
    toast.success("Run ID copiado");
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button onClick={handleCopy} className="flex items-center gap-1.5 group" title="Copiar ID">
      <code className="text-xs font-mono text-primary">{id}</code>
      {copied ? (
        <Check className="h-3 w-3 text-success" />
      ) : (
        <Copy className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
      )}
    </button>
  );
}

export default function ExperimentalPage() {
  const { data, isLoading, isError } = useExperimentalRuns();
  const navigate = useNavigate();

  return (
    <div className="space-y-4 max-w-7xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-foreground">Runs Experimentales</h1>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => navigate("/experimental/compare")}
        >
          <GitCompare className="h-4 w-4" />
          Comparar dos runs
        </Button>
      </div>

      <div className="bg-card border border-border rounded-lg overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[1fr_140px_80px_100px_80px_70px_60px_80px] gap-2 px-4 py-3 border-b border-border text-xs font-medium text-muted-foreground uppercase tracking-wider">
          <span>Run ID</span>
          <span>Fecha</span>
          <span>Bloque</span>
          <span>Queries</span>
          <span>Visibilidad</span>
          <span>SoM</span>
          <span>Citas</span>
          <span></span>
        </div>

        {/* Body */}
        {isLoading ? (
          <div className="divide-y divide-border">
            {[1, 2, 3].map((i) => (
              <div key={i} className="grid grid-cols-[1fr_140px_80px_100px_80px_70px_60px_80px] gap-2 px-4 py-3 items-center">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-5 w-12" />
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-5 w-14" />
                <Skeleton className="h-4 w-12" />
                <Skeleton className="h-4 w-10" />
                <Skeleton className="h-7 w-16" />
              </div>
            ))}
          </div>
        ) : isError || !data ? (
          <div className="py-12 text-center text-muted-foreground text-sm">
            {isError ? "Error al cargar los runs" : "Sin datos disponibles"}
          </div>
        ) : data.items.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground text-sm">
            No hay runs experimentales
          </div>
        ) : (
          <div className="divide-y divide-border">
            {data?.items.map((run) => {
              const successPct = (run.n_successful / run.n_queries) * 100;
              return (
                <div
                  key={run.run_id}
                  className="grid grid-cols-[1fr_140px_80px_100px_80px_70px_60px_80px] gap-2 px-4 py-3 items-center hover:bg-surface-elevated transition-colors"
                >
                  <CopyableId id={run.run_id} />
                  <span className="text-xs text-muted-foreground">{formatDate(run.timestamp)}</span>
                  <div>
                    {run.rotation_block ? (
                      <Badge variant="outline" className="text-[10px] border-primary/40 text-primary font-medium">
                        {run.rotation_block}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-[10px] border-muted-foreground/30 text-muted-foreground">
                        Core
                      </Badge>
                    )}
                  </div>
                  <div className="space-y-1">
                    <span className="text-xs text-foreground">
                      {run.n_successful}/{run.n_queries}
                    </span>
                    <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full", progressColor(successPct))}
                        style={{ width: `${successPct}%` }}
                      />
                    </div>
                  </div>
                  <span className={cn("text-sm font-semibold", visibilityColor(run.visibility_rate))}>
                    {run.visibility_rate.toFixed(1)}%
                  </span>
                  <span className="text-sm text-foreground">{run.avg_som.toFixed(1)}%</span>
                  <span className="text-sm text-muted-foreground">{run.avg_citations.toFixed(1)}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="gap-1 text-xs h-7"
                    onClick={() => navigate(`/experimental/${run.run_id}`)}
                  >
                    <Eye className="h-3.5 w-3.5" />
                    Ver
                  </Button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
