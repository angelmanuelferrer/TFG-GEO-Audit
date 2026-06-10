import { useState } from "react";
import type { LiveQueryResult } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

const ENGINE_TEXT_COLORS: Record<string, string> = {
  gemini: "text-engine-gemini",
  claude: "text-engine-claude",
  openai: "text-engine-openai",
};

interface LiveQueryTableProps {
  results: LiveQueryResult[];
  engines: string[];
}

export function LiveQueryTable({ results, engines }: LiveQueryTableProps) {
  const [selected, setSelected] = useState<LiveQueryResult | null>(null);

  const engineCols = engines.length;

  return (
    <>
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground">Queries ({results.length})</h3>
        </div>

        {/* Header */}
        <div
          className="grid gap-2 px-4 py-2 border-b border-border text-[11px] font-medium text-muted-foreground uppercase tracking-wider items-center"
          style={{
            gridTemplateColumns: `60px 1fr 100px repeat(${engineCols}, 70px) 90px`,
          }}
        >
          <span>ID</span>
          <span>Query</span>
          <span>Categoría</span>
          {engines.map((e) => (
            <span key={e} className={cn("capitalize text-center", ENGINE_TEXT_COLORS[e])}>
              {e}
            </span>
          ))}
          <span className="text-center">Coverage</span>
        </div>

        {/* Rows */}
        {results.map((r) => (
          <div
            key={r.query_id}
            className="grid gap-2 px-4 py-2.5 border-b border-border last:border-0 items-center hover:bg-surface-elevated cursor-pointer transition-colors"
            style={{
              gridTemplateColumns: `60px 1fr 100px repeat(${engineCols}, 70px) 90px`,
            }}
            onClick={() => setSelected(r)}
          >
            <Badge variant="outline" className="text-[10px] font-mono w-fit">{r.query_id}</Badge>
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="text-sm text-foreground truncate">{r.query_text}</span>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-sm text-xs">{r.query_text}</TooltipContent>
            </Tooltip>
            <span className="text-xs text-muted-foreground capitalize">{r.query_category}</span>
            {engines.map((e) => {
              const eng = r.engines[e];
              return (
                <div key={e} className="text-center">
                  {eng?.is_visible ? (
                    <Badge className="bg-success/15 text-success border-success/30 text-[10px] gap-0.5">
                      <Check className="h-3 w-3" />
                    </Badge>
                  ) : (
                    <span className="text-muted-foreground text-xs">–</span>
                  )}
                </div>
              );
            })}
            <div className="flex items-center gap-1.5">
              <div className="h-1.5 flex-1 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${r.engine_coverage}%` }}
                />
              </div>
              <span className="text-[10px] text-muted-foreground w-8 text-right">
                {r.engine_coverage.toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Detail Sheet */}
      <Sheet open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent className="bg-card border-border overflow-y-auto w-[480px] sm:max-w-[480px]">
          {selected && (
            <>
              <SheetHeader>
                <SheetTitle className="text-foreground">
                  <Badge variant="outline" className="font-mono mr-2">{selected.query_id}</Badge>
                  Detalle multi-motor
                </SheetTitle>
              </SheetHeader>
              <div className="space-y-4 mt-4">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Query</p>
                  <p className="text-sm text-foreground">{selected.query_text}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Categoría:</span>
                  <span className="text-sm text-foreground capitalize">{selected.query_category}</span>
                  <span className="text-xs text-muted-foreground ml-auto">Coverage: {selected.engine_coverage.toFixed(1)}%</span>
                </div>

                {/* Engine details side by side */}
                <div className={cn("grid gap-3", engines.length === 1 ? "grid-cols-1" : engines.length === 2 ? "grid-cols-2" : "grid-cols-3")}>
                  {engines.map((engine) => {
                    const eng = selected.engines[engine];
                    return (
                      <div
                        key={engine}
                        className="bg-surface-elevated rounded-lg p-3 space-y-2"
                      >
                        <span className={cn("text-sm font-semibold capitalize", ENGINE_TEXT_COLORS[engine])}>
                          {engine}
                        </span>
                        {eng ? (
                          <>
                            <div className="space-y-1.5 text-xs">
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Visible</span>
                                <span className={eng.is_visible ? "text-success font-medium" : "text-destructive"}>
                                  {eng.is_visible ? "Sí" : "No"}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">SoM</span>
                                <span className="text-foreground font-medium">{eng.som.toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Rank</span>
                                <span className="text-foreground">{eng.first_citation_rank ?? "—"}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Citas</span>
                                <span className="text-foreground">{eng.target_citations}/{eng.total_citations}</span>
                              </div>
                              {eng.sentiment && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Sentiment</span>
                                  <Badge variant="outline" className={cn("text-[8px] px-1 py-0 h-4 leading-none",
                                    eng.sentiment === "POSITIVO" ? "border-success/40 text-success" :
                                    eng.sentiment === "NEGATIVO" ? "border-destructive/40 text-destructive" :
                                    "border-muted-foreground/40 text-muted-foreground"
                                  )}>
                                    {eng.sentiment}
                                  </Badge>
                                </div>
                              )}
                            </div>
                            {eng.brand_mentions.length > 0 && (
                              <div className="pt-1 border-t border-border">
                                <p className="text-[9px] text-muted-foreground uppercase tracking-wide mb-1">
                                  Mentions ({eng.brand_mentions.length})
                                </p>
                                {eng.brand_mentions.map((bm, i) => (
                                  <p key={i} className="text-[10px] text-foreground/70 italic leading-snug">
                                    "{bm.context}"
                                  </p>
                                ))}
                              </div>
                            )}
                          </>
                        ) : (
                          <p className="text-xs text-muted-foreground">Sin datos</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
