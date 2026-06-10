import { useState } from "react";
import { useJobs, useLaunchJob } from "@/api/hooks";
import type { Job, JobStatus } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { FlaskConical, Radio, CheckCircle, XCircle, Clock, Loader2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { Link } from "react-router-dom";

// ── Helpers ───────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: JobStatus }) {
  const map: Record<JobStatus, { label: string; className: string; icon: React.ReactNode }> = {
    pending:  { label: "En cola",    className: "bg-muted text-muted-foreground",              icon: <Clock className="h-3 w-3" /> },
    running:  { label: "Ejecutando", className: "bg-blue-500/15 text-blue-400 border-blue-500/30", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
    done:     { label: "Completado", className: "bg-success/15 text-success border-success/30",     icon: <CheckCircle className="h-3 w-3" /> },
    error:    { label: "Error",      className: "bg-destructive/15 text-destructive border-destructive/30", icon: <XCircle className="h-3 w-3" /> },
  };
  const { label, className, icon } = map[status];
  return (
    <Badge variant="outline" className={cn("gap-1 text-xs", className)}>
      {icon}{label}
    </Badge>
  );
}

function TypeBadge({ type }: { type: "experimental" | "live" }) {
  return type === "experimental"
    ? <Badge variant="outline" className="gap-1 text-xs bg-primary/10 text-primary border-primary/30"><FlaskConical className="h-3 w-3" />Experimental</Badge>
    : <Badge variant="outline" className="gap-1 text-xs bg-[hsl(var(--engine-gemini))]/15 text-engine-gemini border-[hsl(var(--engine-gemini))]/30"><Radio className="h-3 w-3" />Live</Badge>;
}

function paramsLabel(job: Job): string {
  if (job.type === "experimental") {
    const p = job.params as { block: string | null };
    return p.block ? `Bloque ${p.block}` : "Solo core";
  }
  const p = job.params as { engines: string[]; tier: string };
  return `${p.engines.join(", ")} · ${p.tier}`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("es-ES", { dateStyle: "short", timeStyle: "short" });
}

// ── Diálogo Experimental ──────────────────────────────────────────────────────

const BLOCKS = [
  { value: "none", label: "Solo core", desc: "20 queries principales" },
  { value: "R1",   label: "Bloque R1", desc: "Core + 20 queries rotación 1 (40 total)" },
  { value: "R2",   label: "Bloque R2", desc: "Core + 20 queries rotación 2 (40 total)" },
  { value: "R3",   label: "Bloque R3", desc: "Core + 20 queries rotación 3 (40 total)" },
  { value: "R4",   label: "Bloque R4", desc: "Core + 20 queries rotación 4 (40 total)" },
];

function LaunchExperimentalDialog({ onLaunched }: { onLaunched: () => void }) {
  const [open, setOpen] = useState(false);
  const [block, setBlock] = useState<string>("none");
  const launch = useLaunchJob();

  const handleLaunch = () => {
    launch.mutate(
      { type: "experimental", params: { block: block === "none" ? null : block } },
      {
        onSuccess: () => {
          toast.success("Run experimental lanzado");
          setOpen(false);
          onLaunched();
        },
        onError: (e) => toast.error(e.message ?? "Error al lanzar el run"),
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <FlaskConical className="h-4 w-4" />
          Nuevo run experimental
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Lanzar run experimental</DialogTitle>
          <DialogDescription>
            Mide la visibilidad de programamos.es con el vectorstore congelado y RAG Judge.
          </DialogDescription>
        </DialogHeader>

        <div className="py-2">
          <Label className="text-sm font-medium mb-3 block">Selección de queries</Label>
          <RadioGroup value={block} onValueChange={setBlock} className="space-y-2">
            {BLOCKS.map((b) => (
              <div key={b.value} className="flex items-start gap-3 rounded-md border border-border p-3 hover:bg-accent/50 cursor-pointer"
                   onClick={() => setBlock(b.value)}>
                <RadioGroupItem value={b.value} id={`block-${b.value}`} className="mt-0.5" />
                <div>
                  <Label htmlFor={`block-${b.value}`} className="font-medium cursor-pointer">{b.label}</Label>
                  <p className="text-xs text-muted-foreground">{b.desc}</p>
                </div>
              </div>
            ))}
          </RadioGroup>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => setOpen(false)}>Cancelar</Button>
          <Button onClick={handleLaunch} disabled={launch.isPending} className="gap-2">
            {launch.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Lanzar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Diálogo Live ──────────────────────────────────────────────────────────────

const ENGINES = [
  { value: "gemini", label: "Gemini 2.5 Flash" },
  { value: "claude", label: "Claude Haiku 4.5" },
  { value: "openai", label: "GPT-4o mini" },
];

const TIERS = [
  { value: "core",   label: "Core",   desc: "20 queries principales" },
  { value: "light",  label: "Light",  desc: "40 queries (core + R1)" },
  { value: "medium", label: "Medium", desc: "60 queries (core + R1 + R2)" },
  { value: "full",   label: "Full",   desc: "100 queries completas" },
];

function LaunchLiveDialog({ onLaunched }: { onLaunched: () => void }) {
  const [open, setOpen] = useState(false);
  const [engines, setEngines] = useState<string[]>(["gemini", "claude", "openai"]);
  const [tier, setTier] = useState("core");
  const launch = useLaunchJob();

  const toggleEngine = (engine: string) => {
    setEngines((prev) =>
      prev.includes(engine) ? prev.filter((e) => e !== engine) : [...prev, engine]
    );
  };

  const handleLaunch = () => {
    if (engines.length === 0) {
      toast.error("Selecciona al menos un motor");
      return;
    }
    launch.mutate(
      { type: "live", params: { engines, tier } },
      {
        onSuccess: () => {
          toast.success("Evaluación live lanzada");
          setOpen(false);
          onLaunched();
        },
        onError: (e) => toast.error(e.message ?? "Error al lanzar la evaluación"),
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Radio className="h-4 w-4" />
          Nueva evaluación live
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Lanzar evaluación live</DialogTitle>
          <DialogDescription>
            Consulta motores de IA con búsqueda web y mide la visibilidad real.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2">
          <div>
            <Label className="text-sm font-medium mb-3 block">Motores</Label>
            <div className="space-y-2">
              {ENGINES.map((e) => (
                <div key={e.value} className="flex items-center gap-3 rounded-md border border-border p-3 hover:bg-accent/50 cursor-pointer"
                     onClick={() => toggleEngine(e.value)}>
                  <Checkbox
                    id={`eng-${e.value}`}
                    checked={engines.includes(e.value)}
                    onCheckedChange={() => toggleEngine(e.value)}
                  />
                  <Label htmlFor={`eng-${e.value}`} className="cursor-pointer">{e.label}</Label>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          <div>
            <Label className="text-sm font-medium mb-3 block">Tier de queries</Label>
            <RadioGroup value={tier} onValueChange={setTier} className="space-y-2">
              {TIERS.map((t) => (
                <div key={t.value} className="flex items-start gap-3 rounded-md border border-border p-3 hover:bg-accent/50 cursor-pointer"
                     onClick={() => setTier(t.value)}>
                  <RadioGroupItem value={t.value} id={`tier-${t.value}`} className="mt-0.5" />
                  <div>
                    <Label htmlFor={`tier-${t.value}`} className="font-medium cursor-pointer">{t.label}</Label>
                    <p className="text-xs text-muted-foreground">{t.desc}</p>
                  </div>
                </div>
              ))}
            </RadioGroup>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => setOpen(false)}>Cancelar</Button>
          <Button onClick={handleLaunch} disabled={launch.isPending || engines.length === 0} className="gap-2">
            {launch.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Lanzar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Job row ───────────────────────────────────────────────────────────────────

function JobRow({ job }: { job: Job }) {
  const [showOutput, setShowOutput] = useState(false);

  const runLink = job.run_id
    ? job.type === "experimental"
      ? `/experimental/${job.run_id}`
      : `/live`
    : null;

  return (
    <div className="border-b border-border last:border-0">
      <div className="flex items-center gap-3 px-4 py-3">
        <TypeBadge type={job.type} />
        <StatusBadge status={job.status} />

        <span className="text-sm text-muted-foreground flex-1">{paramsLabel(job)}</span>

        <span className="text-xs text-muted-foreground hidden sm:block">{formatDate(job.created_at)}</span>

        {runLink && (
          <Link to={runLink} className="text-xs text-primary hover:underline flex items-center gap-1">
            <ExternalLink className="h-3 w-3" />
            {job.run_id}
          </Link>
        )}

        {job.output && (
          <Button variant="ghost" size="sm" className="h-7 text-xs"
                  onClick={() => setShowOutput(!showOutput)}>
            {showOutput ? "Ocultar logs" : "Ver logs"}
          </Button>
        )}
      </div>

      {showOutput && job.output && (
        <ScrollArea className="h-48 mx-4 mb-3 rounded border border-border bg-muted/30">
          <pre className="p-3 text-xs font-mono text-muted-foreground whitespace-pre-wrap break-all leading-relaxed">
            {job.output}
          </pre>
        </ScrollArea>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function JobsPage() {
  const hasRunning = true;
  const { data, isLoading, refetch } = useJobs(hasRunning);

  const jobs = data?.items ?? [];
  const actuallyRunning = jobs.some((j) => j.status === "pending" || j.status === "running");

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Pipeline Runner</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Lanza runs experimentales y evaluaciones live desde el dashboard.
        </p>
      </div>

      {/* Lanzadores */}
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Experimental */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <FlaskConical className="h-4 w-4 text-primary" />
              Experimental
            </CardTitle>
            <CardDescription className="text-xs">
              Mide visibilidad GEO con vectorstore congelado + RAG Judge (Gemini).
              Requiere <code>frozen_vectorstore/</code> en disco.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LaunchExperimentalDialog onLaunched={refetch} />
          </CardContent>
        </Card>

        {/* Live */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Radio className="h-4 w-4 text-engine-gemini" />
              Live Multi-motor
            </CardTitle>
            <CardDescription className="text-xs">
              Consulta Gemini, Claude y OpenAI con búsqueda web en tiempo real.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LaunchLiveDialog onLaunched={refetch} />
          </CardContent>
        </Card>
      </div>

      {/* Lista de jobs */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              Historial de jobs
              {actuallyRunning && (
                <Badge variant="outline" className="ml-2 text-xs bg-blue-500/15 text-blue-400 border-blue-500/30 gap-1">
                  <Loader2 className="h-3 w-3 animate-spin" />En curso
                </Badge>
              )}
            </CardTitle>
            <span className="text-xs text-muted-foreground">{jobs.length} jobs</span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-20 text-muted-foreground text-sm gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />Cargando...
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex items-center justify-center h-20 text-muted-foreground text-sm">
              No hay jobs todavía. Lanza uno desde arriba.
            </div>
          ) : (
            jobs.map((job) => <JobRow key={job.job_id} job={job} />)
          )}
        </CardContent>
      </Card>
    </div>
  );
}
