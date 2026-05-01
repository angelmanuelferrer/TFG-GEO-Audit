import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Sparkles, ChevronRight, Copy, Check, FlaskConical, Radio } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const headers = import.meta.env.VITE_API_KEY
  ? { "X-Api-Key": import.meta.env.VITE_API_KEY }
  : {};

type PriorityQuery = {
  query_id: string;
  query_text: string;
  score: number;
  reason: string;
  competitors_cited: { url: string; excerpt: string }[];
  relevant_urls: string[];
};

type PrioritizeResponse = {
  mode: string;
  run_id: string;
  queries: PriorityQuery[];
};

type Recommendation = {
  title: string;
  lever: string;
  where: string;
  why: string;
  evidence: string;
  impact: string;
  target_query_ids: string[];
};

type AnalyzeResponse = {
  recommendations_l1: Recommendation[];
  prompt_l2: string;
  _parse_error?: string;
};

async function fetchPrioritize(mode: string): Promise<PrioritizeResponse> {
  const { data } = await axios.get(`${API}/api/optimizer/prioritize`, {
    params: { mode },
    headers,
  });
  return data;
}

async function postAnalyze({ ids, mode }: { ids: string[]; mode: string }): Promise<AnalyzeResponse> {
  const { data } = await axios.post(`${API}/api/optimizer/analyze`, { query_ids: ids, mode }, { headers });
  return data;
}

function QueryRow({
  q,
  selected,
  onSelect,
}: {
  q: PriorityQuery;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <div
      className={`cursor-pointer rounded-lg border p-4 transition-colors ${
        selected ? "border-primary bg-primary/5" : "border-border hover:border-primary/40 hover:bg-accent/40"
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className="text-xs font-mono shrink-0">
              {q.query_id}
            </Badge>
            <Badge
              className={`text-xs shrink-0 ${
                q.score >= 3 ? "bg-red-100 text-red-700" : q.score >= 2 ? "bg-yellow-100 text-yellow-700" : "bg-blue-100 text-blue-700"
              }`}
              variant="secondary"
            >
              {q.score >= 3 ? "Alta" : q.score >= 2 ? "Media" : "Baja"} prioridad
            </Badge>
          </div>
          <p className="text-sm font-medium truncate">{q.query_text}</p>
          <p className="text-xs text-muted-foreground mt-1">{q.reason}</p>
        </div>
        <ChevronRight className={`h-4 w-4 shrink-0 text-muted-foreground mt-1 transition-transform ${selected ? "rotate-90 text-primary" : ""}`} />
      </div>

      {selected && (
        <div className="mt-3 space-y-2 border-t pt-3 overflow-hidden">
          {q.competitors_cited.slice(0, 2).map((c, i) => (
            <div key={i} className="rounded bg-muted/60 p-2 text-xs overflow-hidden">
              <p className="font-medium text-muted-foreground truncate">{c.url}</p>
              <p className="mt-0.5 italic line-clamp-3 break-words">"{c.excerpt}"</p>
            </div>
          ))}
          {q.relevant_urls.length > 0 && (
            <div className="text-xs text-muted-foreground overflow-hidden">
              <span className="font-medium">Tus páginas: </span>
              {q.relevant_urls.slice(0, 2).map((u, i) => (
                <span key={i} className="font-mono text-primary break-all text-[10px]">
                  {u.replace("https://programamos.es", "")}{i < Math.min(q.relevant_urls.length, 2) - 1 ? ", " : ""}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PriorityPanel({
  mode,
  onAnalyze,
  analyzing,
}: {
  mode: string;
  onAnalyze: (ids: string[], mode: string) => void;
  analyzing: boolean;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [checkedIds, setCheckedIds] = useState<Set<string>>(new Set());

  const { data, isLoading, error } = useQuery({
    queryKey: ["prioritize", mode],
    queryFn: () => fetchPrioritize(mode),
  });

  function toggleCheck(id: string) {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  if (isLoading) return <div className="space-y-3">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>;
  if (error) return <p className="text-sm text-destructive">Error cargando datos. ¿Está el backend activo?</p>;
  if (!data?.queries?.length) return <p className="text-sm text-muted-foreground">No hay queries priorizadas disponibles.</p>;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-xs text-muted-foreground">
          <span className="font-mono text-foreground">{data.run_id}</span> · {data.queries.length} queries a mejorar
        </p>
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCheckedIds(new Set(data.queries.map((q) => q.query_id)))}
          >
            Todas
          </Button>
          <Button
            size="sm"
            disabled={checkedIds.size === 0 || analyzing}
            onClick={() => onAnalyze([...checkedIds], mode)}
          >
            <Sparkles className="h-3.5 w-3.5 mr-1.5" />
            {analyzing ? "Analizando…" : `Analizar${checkedIds.size > 0 ? ` (${checkedIds.size})` : ""}`}
          </Button>
        </div>
      </div>

      <div className="space-y-1.5">
        {data.queries.map((q) => (
          <div key={q.query_id} className="flex gap-2 min-w-0">
            <input
              type="checkbox"
              className="mt-4 shrink-0 accent-primary"
              checked={checkedIds.has(q.query_id)}
              onChange={() => toggleCheck(q.query_id)}
            />
            <div className="flex-1 min-w-0">
              <QueryRow
                q={q}
                selected={selected === q.query_id}
                onSelect={() => setSelected(selected === q.query_id ? null : q.query_id)}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RecommendationsPanel({ data }: { data: AnalyzeResponse }) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  function copyPrompt() {
    navigator.clipboard.writeText(data.prompt_l2);
    setCopied(true);
    toast({ title: "Prompt copiado", description: "Pégalo en Claude Code apuntando al repo del sitio." });
    setTimeout(() => setCopied(false), 2000);
  }

  const leverLabel: Record<string, string> = {
    citation_readiness: "Citabilidad",
    authority_injection: "Autoridad",
    low_perplexity: "Baja perplejidad",
    machine_scannability: "Escaneabilidad",
    semantic_clarity: "Claridad semántica",
    caption_injection: "Inyección de captions",
  };

  return (
    <div className="space-y-6">
      {data._parse_error && (
        <p className="text-xs text-destructive border border-destructive/30 rounded p-2">
          ⚠ {data._parse_error}
        </p>
      )}
      <div>
        <h3 className="font-semibold mb-3">
          Recomendaciones priorizadas
          {data.recommendations_l1.length > 0 && (
            <span className="ml-2 text-xs font-normal text-muted-foreground">({data.recommendations_l1.length})</span>
          )}
        </h3>
        {data.recommendations_l1.length === 0 && !data._parse_error && (
          <p className="text-sm text-muted-foreground">No se generaron recomendaciones.</p>
        )}
        <div className="space-y-3">
          {data.recommendations_l1.map((r, i) => (
            <Card key={i}>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-start gap-3">
                  <span className="h-6 w-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0 space-y-1.5">
                    <p className="font-medium text-sm">{r.title}</p>
                    <div className="flex flex-wrap gap-1.5">
                      <Badge variant="outline" className={`text-xs ${r.impact === "alto" ? "border-green-500 text-green-700" : r.impact === "medio" ? "border-yellow-500 text-yellow-700" : "border-blue-500 text-blue-700"}`}>
                        Impacto {r.impact}
                      </Badge>
                      {r.lever && (
                        <Badge variant="secondary" className="text-xs font-mono">
                          {leverLabel[r.lever] ?? r.lever}
                        </Badge>
                      )}
                      {r.target_query_ids?.map((qid) => (
                        <Badge key={qid} variant="outline" className="text-xs font-mono text-muted-foreground">
                          {qid}
                        </Badge>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground"><span className="font-medium">Dónde:</span> {r.where}</p>
                    <p className="text-xs text-muted-foreground"><span className="font-medium">Por qué:</span> {r.why}</p>
                    <p className="text-xs italic text-muted-foreground line-clamp-2"><span className="font-medium not-italic">Evidencia:</span> "{r.evidence}"</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">Prompt para Claude Code (L2)</h3>
          <Button variant="outline" size="sm" onClick={copyPrompt}>
            {copied ? <Check className="h-4 w-4 mr-1.5" /> : <Copy className="h-4 w-4 mr-1.5" />}
            {copied ? "Copiado" : "Copiar prompt"}
          </Button>
        </div>
        <pre className="rounded-lg bg-muted p-4 text-xs overflow-auto max-h-64 whitespace-pre-wrap font-mono">
          {typeof data.prompt_l2 === "string"
            ? data.prompt_l2
            : JSON.stringify(data.prompt_l2, null, 2)}
        </pre>
      </div>
    </div>
  );
}

export default function OptimizerPage() {
  const { toast } = useToast();
  const [results, setResults] = useState<AnalyzeResponse | null>(null);

  const analyzeMutation = useMutation({
    mutationFn: ({ ids, mode }: { ids: string[]; mode: string }) => postAnalyze({ ids, mode }),
    onSuccess: (data) => {
      setResults(data);
      toast({ title: "Análisis completado", description: "Revisa las recomendaciones." });
    },
    onError: (err: unknown) => {
      const status = (err as { response?: { status?: number; data?: { detail?: string } } })?.response?.status;
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      if (status === 429 || status === 503) {
        toast({ title: "Gemini no disponible", description: detail ?? "Cuota agotada o alta demanda. Espera un momento e inténtalo de nuevo.", variant: "destructive" });
      } else {
        toast({ title: "Error al analizar", description: detail ?? "Revisa que el backend está activo y tiene ANTHROPIC_API_KEY configurada.", variant: "destructive" });
      }
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          Optimizer
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Detecta las queries donde programamos.es pierde visibilidad y genera recomendaciones accionables.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Queries a mejorar</CardTitle>
            <CardDescription>
              Queries donde tienes margen de mejora. Selecciona las que quieres analizar.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="experimental">
              <TabsList className="mb-4">
                <TabsTrigger value="experimental" className="gap-1.5">
                  <FlaskConical className="h-3.5 w-3.5" />
                  Experimental
                </TabsTrigger>
                <TabsTrigger value="live" className="gap-1.5">
                  <Radio className="h-3.5 w-3.5" />
                  Live
                </TabsTrigger>
              </TabsList>
              <TabsContent value="experimental">
                <PriorityPanel
                  mode="experimental"
                  onAnalyze={(ids, mode) => analyzeMutation.mutate({ ids, mode })}
                  analyzing={analyzeMutation.isPending}
                />
              </TabsContent>
              <TabsContent value="live">
                <PriorityPanel
                  mode="live"
                  onAnalyze={(ids, mode) => analyzeMutation.mutate({ ids, mode })}
                  analyzing={analyzeMutation.isPending}
                />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recomendaciones</CardTitle>
            <CardDescription>
              El agente analiza el contenido de tus páginas frente a los competidores citados.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {analyzeMutation.isPending && (
              <div className="space-y-3">
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
              </div>
            )}
            {!analyzeMutation.isPending && !results && (
              <div className="flex flex-col items-center justify-center py-12 text-center gap-3">
                <Sparkles className="h-8 w-8 text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground">
                  Selecciona queries en el panel izquierdo y haz clic en <strong>Analizar</strong>.
                </p>
              </div>
            )}
            {results && <RecommendationsPanel data={results} />}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
