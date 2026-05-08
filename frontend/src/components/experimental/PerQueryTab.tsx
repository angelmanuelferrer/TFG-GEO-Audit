import { useState } from "react";
import type { PerQueryMetric } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

export function PerQueryTab({ metrics }: { metrics: PerQueryMetric[] }) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<PerQueryMetric | null>(null);

  const filtered = metrics.filter(
    (m) =>
      m.query.toLowerCase().includes(search.toLowerCase()) ||
      (m.query_id ?? "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <div className="space-y-3">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar query..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-surface-elevated border-border"
          />
        </div>

        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="grid grid-cols-[60px_1fr_100px_70px_60px_50px_60px_60px] gap-2 px-4 py-2.5 border-b border-border text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
            <span>ID</span>
            <span>Query</span>
            <span>Categoría</span>
            <span>Visible</span>
            <span>SoM%</span>
            <span>Rank</span>
            <span>PAWC</span>
            <span>Citas</span>
          </div>
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground text-sm">
              No se encontraron queries
            </div>
          ) : (
            filtered.map((m) =>
              m.error ? (
                <div
                  key={m.query_id}
                  className="grid grid-cols-[60px_1fr_100px_70px_60px_50px_60px_60px] gap-2 px-4 py-2.5 items-center border-b border-border last:border-0 bg-destructive/5"
                >
                  <Badge variant="outline" className="text-[10px] font-mono w-fit border-destructive/40 text-destructive">
                    {m.query_id}
                  </Badge>
                  <span className="text-sm text-muted-foreground truncate col-span-7 italic">{m.error}</span>
                </div>
              ) : (
                <div
                  key={m.query_id}
                  className="grid grid-cols-[60px_1fr_100px_70px_60px_50px_60px_60px] gap-2 px-4 py-2.5 items-center border-b border-border last:border-0 hover:bg-surface-elevated cursor-pointer transition-colors"
                  onClick={() => setSelected(m)}
                >
                  <Badge variant="outline" className="text-[10px] font-mono w-fit">
                    {m.query_id}
                  </Badge>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-sm text-foreground truncate">{m.query}</span>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-sm text-xs">
                      {m.query}
                    </TooltipContent>
                  </Tooltip>
                  <span className="text-xs text-muted-foreground capitalize">{m.category}</span>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-[10px] w-fit",
                      m.is_visible
                        ? "border-success/40 text-success"
                        : "border-destructive/40 text-destructive"
                    )}
                  >
                    {m.is_visible ? "Sí" : "No"}
                  </Badge>
                  <span className="text-sm text-foreground">{m.som.toFixed(1)}</span>
                  <span className="text-sm text-muted-foreground">{m.first_citation_rank ?? "—"}</span>
                  <span className="text-sm text-muted-foreground">{m.pawc.toFixed(1)}</span>
                  <span className="text-sm text-muted-foreground">{m.target_citations}/{m.total_citations}</span>
                </div>
              )
            )
          )}
        </div>
      </div>

      {/* Detail Sheet */}
      <Sheet open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent className="bg-card border-border overflow-y-auto w-[420px] sm:max-w-[420px]">
          {selected && (
            <>
              <SheetHeader>
                <SheetTitle className="text-foreground">
                  <Badge variant="outline" className="font-mono mr-2">{selected.query_id}</Badge>
                  Detalle de query
                </SheetTitle>
              </SheetHeader>
              <div className="space-y-5 mt-4">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Query</p>
                  <p className="text-sm text-foreground">{selected.query}</p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-surface-elevated rounded-md p-3">
                    <p className="text-[10px] text-muted-foreground uppercase">Categoría</p>
                    <p className="text-sm text-foreground capitalize">{selected.category}</p>
                  </div>
                  <div className="bg-surface-elevated rounded-md p-3">
                    <p className="text-[10px] text-muted-foreground uppercase">Visible</p>
                    <p className={cn("text-sm font-medium", selected.is_visible ? "text-success" : "text-destructive")}>
                      {selected.is_visible ? "Sí" : "No"}
                    </p>
                  </div>
                  <div className="bg-surface-elevated rounded-md p-3">
                    <p className="text-[10px] text-muted-foreground uppercase">SoM</p>
                    <p className="text-sm text-foreground font-semibold">{selected.som.toFixed(1)}%</p>
                  </div>
                  <div className="bg-surface-elevated rounded-md p-3">
                    <p className="text-[10px] text-muted-foreground uppercase">Rank</p>
                    <p className="text-sm text-foreground">{selected.first_citation_rank ?? "—"}</p>
                  </div>
                  <div className="bg-surface-elevated rounded-md p-3">
                    <p className="text-[10px] text-muted-foreground uppercase">PAWC</p>
                    <p className="text-sm text-foreground">{selected.pawc.toFixed(1)}</p>
                  </div>
                  <div className="bg-surface-elevated rounded-md p-3">
                    <p className="text-[10px] text-muted-foreground uppercase">Citation Rate</p>
                    <p className="text-sm text-foreground">
                      {selected.citation_rate != null ? selected.citation_rate.toFixed(1) + "%" : "—"}
                    </p>
                  </div>
                  <div className="bg-surface-elevated rounded-md p-3">
                    <p className="text-[10px] text-muted-foreground uppercase">Citas target</p>
                    <p className="text-sm text-foreground">{selected.target_citations}/{selected.total_citations}</p>
                  </div>
                </div>

                {/* Brand mentions */}
                {selected.brand_mentions.length > 0 && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2 font-medium uppercase tracking-wide">
                      Brand Mentions ({selected.brand_mentions.length})
                    </p>
                    <div className="space-y-2">
                      {selected.brand_mentions.map((bm, i) => (
                        <div key={i} className="bg-surface-elevated rounded-md p-3 space-y-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-[10px]">{bm.source}</Badge>
                            <span className="text-[10px] text-muted-foreground">pos: {bm.position}</span>
                          </div>
                          <p className="text-xs text-foreground/80 italic">"{bm.context}"</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
