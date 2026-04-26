import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string;
  delta?: number | null;
  suffix?: string;
  subtitle?: string;
  loading?: boolean;
}

export function KpiCard({ label, value, delta, suffix, subtitle, loading }: KpiCardProps) {
  if (loading) {
    return (
      <div className="bg-card border border-border rounded-lg p-5 space-y-3">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-3 w-16" />
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-5 flex flex-col gap-1 relative overflow-hidden">
      <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-foreground">
        {value}
        {suffix && <span className="text-lg text-muted-foreground ml-0.5">{suffix}</span>}
      </p>
      {delta != null && (
        <div className="flex items-center gap-1">
          {delta >= 0 ? (
            <TrendingUp className="h-3.5 w-3.5 text-success" />
          ) : (
            <TrendingDown className="h-3.5 w-3.5 text-destructive" />
          )}
          <span
            className={cn(
              "text-xs font-medium",
              delta >= 0 ? "text-success" : "text-destructive"
            )}
          >
            {delta >= 0 ? "+" : ""}
            {delta.toFixed(2)}
          </span>
        </div>
      )}
      {subtitle && <p className="text-[11px] text-muted-foreground">{subtitle}</p>}
      {/* Static sparkline placeholder */}
      <svg className="absolute bottom-0 right-0 w-20 h-10 opacity-20" viewBox="0 0 80 40">
        <polyline
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth="2"
          points="0,30 10,25 20,28 30,18 40,22 50,15 60,20 70,12 80,16"
        />
      </svg>
    </div>
  );
}
