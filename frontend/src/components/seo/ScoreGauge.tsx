import { cn } from "@/lib/utils";
import { RadialBarChart, RadialBar, ResponsiveContainer } from "recharts";

interface GaugeProps {
  value: number;
  label: string;
  maxValue?: number;
}

function gaugeColor(value: number) {
  if (value >= 90) return "hsl(160 84% 39%)";
  if (value >= 50) return "hsl(38 92% 50%)";
  return "hsl(0 84% 60%)";
}

function gaugeTextClass(value: number) {
  if (value >= 90) return "text-success";
  if (value >= 50) return "text-warning";
  return "text-destructive";
}

export function ScoreGauge({ value, label, maxValue = 100 }: GaugeProps) {
  const pct = (value / maxValue) * 100;
  const data = [{ value: pct, fill: gaugeColor(value) }];

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-28 h-28">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="70%"
            outerRadius="100%"
            startAngle={225}
            endAngle={-45}
            data={data}
            barSize={8}
          >
            <RadialBar
              dataKey="value"
              background={{ fill: "hsl(213 40% 22%)" }}
              cornerRadius={4}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn("text-2xl font-bold", gaugeTextClass(value))}>
            {Math.round(value)}
          </span>
        </div>
      </div>
      <span className="text-xs text-muted-foreground mt-1 font-medium">{label}</span>
    </div>
  );
}
