import React from "react";
import type { CoverageMatrixResponse } from "@/api/types";

function heatColor(value: number): string {
  // 0=dark red, 50=yellow, 100=green
  if (value <= 0) return "hsl(0, 60%, 20%)";
  if (value <= 25) return `hsl(${value * 1.2}, 70%, ${25 + value * 0.3}%)`;
  if (value <= 50) return `hsl(${30 + (value - 25) * 0.8}, 75%, ${30 + value * 0.2}%)`;
  if (value <= 75) return `hsl(${50 + (value - 50) * 1.6}, 65%, ${35 + (value - 50) * 0.3}%)`;
  return `hsl(${130 + (value - 75) * 0.4}, 60%, ${35 + (value - 75) * 0.2}%)`;
}

const ENGINE_LABELS: Record<string, string> = {
  gemini: "Gemini",
  claude: "Claude",
  openai: "OpenAI",
};

export function CoverageHeatmap({ matrix }: { matrix: CoverageMatrixResponse }) {
  return (
    <div className="bg-card border border-border rounded-lg p-5 space-y-3">
      <h3 className="text-sm font-semibold text-foreground">Heatmap: Categoría × Motor</h3>
      <div className="overflow-x-auto">
        <div
          className="grid gap-1"
          style={{
            gridTemplateColumns: `120px repeat(${matrix.engines.length}, 1fr)`,
          }}
        >
          {/* Header row */}
          <div />
          {matrix.engines.map((e) => (
            <div key={e} className="text-center text-xs font-medium text-muted-foreground py-2 capitalize">
              {ENGINE_LABELS[e] ?? e}
            </div>
          ))}

          {/* Data rows */}
          {matrix.categories.map((cat) => (
            <React.Fragment key={cat}>
              <div className="flex items-center text-sm text-foreground capitalize font-medium px-2">
                {cat}
              </div>
              {matrix.engines.map((engine) => {
                const val = matrix.matrix[cat]?.[engine] ?? 0;
                return (
                  <div
                    key={`${cat}-${engine}`}
                    className="rounded-md flex items-center justify-center py-4 text-sm font-bold"
                    style={{ backgroundColor: heatColor(val), color: "#f1f5f9" }}
                  >
                    {val.toFixed(0)}%
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}
