import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus, Star, Copy, Check } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

// === DeltaIndicator ===
export function DeltaIndicator({ value, suffix = "" }: { value: number | null | undefined; suffix?: string }) {
  if (value == null) return <span className="text-xs text-muted-foreground">—</span>;
  const isPositive = value >= 0;
  const Icon = value === 0 ? Minus : isPositive ? TrendingUp : TrendingDown;
  return (
    <span className={cn("inline-flex items-center gap-0.5 text-xs font-medium", isPositive ? "text-success" : "text-destructive")}>
      <Icon className="h-3 w-3" />
      {isPositive ? "+" : ""}{value.toFixed(2)}{suffix}
    </span>
  );
}

// === MetricBadge ===
export function MetricBadge({ visible }: { visible: boolean }) {
  return (
    <Badge variant="outline" className={cn("text-[10px]", visible ? "border-success/40 text-success" : "border-destructive/40 text-destructive")}>
      {visible ? "Visible" : "No visible"}
    </Badge>
  );
}

// === EngineTag ===
const ENGINE_STYLES: Record<string, string> = {
  gemini: "bg-[hsl(var(--engine-gemini))]/15 text-engine-gemini",
  claude: "bg-[hsl(var(--engine-claude))]/15 text-engine-claude",
  openai: "bg-[hsl(var(--engine-openai))]/15 text-engine-openai",
};

export function EngineTag({ engine }: { engine: string }) {
  return (
    <Badge className={cn("text-[10px] border-0 capitalize", ENGINE_STYLES[engine] ?? "bg-muted text-foreground")}>
      {engine}
    </Badge>
  );
}

// === RunIdBadge ===
export function RunIdBadge({ id }: { id: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(id);
    setCopied(true);
    toast.success("ID copiado");
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button onClick={handleCopy} className="inline-flex items-center gap-1 group" title="Copiar">
      <code className="text-xs font-mono text-primary">{id}</code>
      {copied ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />}
    </button>
  );
}

// === CategoryBadge ===
const CAT_STYLES: Record<string, { bg: string; text: string }> = {
  informacional: { bg: "bg-primary/10", text: "text-primary" },
  comparativa: { bg: "bg-secondary/10", text: "text-secondary" },
  navegacional: { bg: "bg-success/10", text: "text-success" },
};

export function CategoryBadge({ category }: { category: string }) {
  const s = CAT_STYLES[category] ?? { bg: "bg-muted", text: "text-foreground" };
  return <Badge className={cn("text-[10px] border-0 capitalize", s.bg, s.text)}>{category}</Badge>;
}

// === SemaphoreIndicator ===
export function SemaphoreIndicator({ value, thresholds, unit }: { value: number; thresholds: [number, number]; unit: string }) {
  const color = value <= thresholds[0] ? "text-success" : value <= thresholds[1] ? "text-warning" : "text-destructive";
  return <span className={cn("text-sm font-semibold", color)}>{value}{unit}</span>;
}

// === OriginalStar ===
export function OriginalStar({ is: isOriginal }: { is: boolean }) {
  if (!isOriginal) return null;
  return <Star className="h-3.5 w-3.5 text-warning fill-warning" />;
}
