import { useState, useMemo } from "react";
import type { RawResponse, PerQueryMetric } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, ChevronLeft, ChevronRight } from "lucide-react";

const PAGE_SIZE = 10;
const CATEGORIES = ["todas", "informacional", "comparativa", "navegacional"];

interface RawTabProps {
  data: RawResponse | undefined;
  perQueryMetrics?: PerQueryMetric[];
}

export function RawTab({ data, perQueryMetrics = [] }: RawTabProps) {
  const [category, setCategory] = useState("todas");
  const [page, setPage] = useState(0);

  // Build query_id → category map from scorecard
  const categoryMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const q of perQueryMetrics) {
      if (q.query_id && q.category) map[q.query_id] = q.category;
    }
    return map;
  }, [perQueryMetrics]);

  const filtered = useMemo(() => {
    if (!data) return [];
    if (category === "todas") return data.items;
    return data.items.filter((item) => {
      const cat = item.query_id ? categoryMap[item.query_id] : undefined;
      return cat === category;
    });
  }, [data, category, categoryMap]);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pageItems = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  function handleCategory(cat: string) {
    setCategory(cat);
    setPage(0);
  }

  if (!data || data.items.length === 0) {
    return <div className="text-muted-foreground text-sm py-8 text-center">Sin respuestas raw disponibles</div>;
  }

  return (
    <div className="space-y-4">
      {/* Category filter */}
      <div className="flex gap-2 flex-wrap">
        {CATEGORIES.map((cat) => (
          <Button
            key={cat}
            variant={category === cat ? "default" : "outline"}
            size="sm"
            className="capitalize text-xs"
            onClick={() => handleCategory(cat)}
          >
            {cat}
          </Button>
        ))}
      </div>

      {/* Count */}
      <p className="text-xs text-muted-foreground">
        Mostrando {pageItems.length} de {filtered.length} respuestas
        {category !== "todas" && ` (${category})`}
      </p>

      {/* Items */}
      {pageItems.map((item) => (
        <RawCard key={item.query_id} item={item} category={item.query_id ? categoryMap[item.query_id] : undefined} />
      ))}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
          </Button>
          <span className="text-xs text-muted-foreground">
            Página {page + 1} de {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
}

function RawCard({ item, category }: { item: RawResponse["items"][0]; category?: string }) {
  const [expanded, setExpanded] = useState(false);

  if (item.error) {
    return (
      <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-[10px] border-destructive/40 text-destructive">{item.query_id}</Badge>
          {category && <Badge variant="secondary" className="text-[10px]">{category}</Badge>}
          <span className="text-sm text-muted-foreground">{item.query}</span>
        </div>
        <p className="text-xs text-destructive italic">{item.error}</p>
      </div>
    );
  }

  const response = item.answer?.answer ?? "";
  const citations = item.answer?.citations ?? [];
  const truncated = response.length > 200;
  const displayText = expanded ? response : response.slice(0, 200);

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <Badge variant="outline" className="font-mono text-[10px]">{item.query_id}</Badge>
        {category && <Badge variant="secondary" className="text-[10px]">{category}</Badge>}
        <span className="text-sm text-foreground font-medium">{item.query}</span>
      </div>
      <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
        {displayText}{truncated && !expanded && "..."}
      </div>
      {truncated && (
        <Button type="button" variant="link" size="sm" className="text-primary h-auto p-0" onClick={() => setExpanded(!expanded)}>
          {expanded ? "ver menos" : "ver más"}
        </Button>
      )}
      {citations.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide font-medium">
            Citations ({citations.length})
          </p>
          {citations.map((c, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <ExternalLink className="h-3 w-3 text-primary mt-0.5 shrink-0" />
              <div>
                <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline break-all">
                  {c.url}
                </a>
                <p className="text-muted-foreground">{c.quote}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
