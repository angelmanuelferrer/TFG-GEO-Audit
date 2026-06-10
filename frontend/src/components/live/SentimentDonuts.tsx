import type { SentimentDistribution } from "@/api/types";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const SENTIMENT_COLORS: Record<string, string> = {
  POSITIVO: "hsl(160 84% 39%)",
  NEUTRO: "hsl(215 20% 50%)",
  NEGATIVO: "hsl(350 70% 55%)",
  null: "hsl(215 15% 30%)",
};

const ENGINE_COLORS: Record<string, string> = {
  gemini: "hsl(var(--engine-gemini))",
  claude: "hsl(var(--engine-claude))",
  openai: "hsl(var(--engine-openai))",
};

export function SentimentDonuts({ data }: { data: SentimentDistribution[] }) {
  // Filter engines with any sentiment data
  const withData = data.filter((d) => d.POSITIVO + d.NEUTRO + d.NEGATIVO + d.null > 0);
  if (withData.length === 0) return null;

  return (
    <div className="bg-card border border-border rounded-lg p-5 space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Distribución de Sentiment por Motor</h3>
      <div className="flex flex-wrap gap-6 justify-center">
        {withData.map((eng) => {
          const chartData = [
            { name: "Positivo", value: eng.POSITIVO },
            { name: "Neutro", value: eng.NEUTRO },
            { name: "Negativo", value: eng.NEGATIVO },
            { name: "No citado", value: eng.null },
          ].filter((d) => d.value > 0);

          const colors = [
            SENTIMENT_COLORS.POSITIVO,
            SENTIMENT_COLORS.NEUTRO,
            SENTIMENT_COLORS.NEGATIVO,
            SENTIMENT_COLORS.null,
          ];

          return (
            <div key={eng.engine} className="flex flex-col items-center">
              <span
                className="text-sm font-semibold capitalize mb-1"
                style={{ color: ENGINE_COLORS[eng.engine] ?? "hsl(var(--foreground))" }}
              >
                {eng.engine}
              </span>
              <ResponsiveContainer width={130} height={130}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={55}
                    paddingAngle={3}
                    dataKey="value"
                    stroke="none"
                  >
                    {chartData.map((entry, idx) => {
                      const colorKey = entry.name === "Positivo" ? "POSITIVO" : entry.name === "Neutro" ? "NEUTRO" : entry.name === "Negativo" ? "NEGATIVO" : "null"; // "No citado" → "null"
                      return <Cell key={idx} fill={SENTIMENT_COLORS[colorKey] ?? colors[idx]} />;
                    })}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: "hsl(222 45% 10%)", border: "1px solid hsl(213 40% 22%)", borderRadius: "8px", fontSize: "11px", color: "hsl(215 20% 85%)" }}
                    labelStyle={{ color: "hsl(215 20% 85%)" }}
                    itemStyle={{ color: "hsl(215 20% 85%)" }}
                    formatter={(value: number, name: string) => [value, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          );
        })}
      </div>
      {/* Legend */}
      <div className="flex justify-center gap-4">
        {[
          { label: "Positivo", color: SENTIMENT_COLORS.POSITIVO },
          { label: "Neutro", color: SENTIMENT_COLORS.NEUTRO },
          { label: "Negativo", color: SENTIMENT_COLORS.NEGATIVO },
          { label: "No citado", color: SENTIMENT_COLORS.null },
        ].map((l) => (
          <div key={l.label} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: l.color }} />
            <span className="text-[10px] text-muted-foreground">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
