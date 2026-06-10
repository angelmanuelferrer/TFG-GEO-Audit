import { useLocation } from "react-router-dom";

const routeLabels: Record<string, string> = {
  "/": "Home",
  "/experimental": "Runs Experimentales",
  "/experimental/compare": "Comparar Runs",
  "/live": "Live Multi-motor",
  "/seo": "SEO Histórico",
  "/timeline": "Series Temporales",
  "/queries": "Queries Explorer",
  "/jobs": "Jobs",
  "/metrics-catalog": "Catálogo de Métricas",
};

export function AppHeader() {
  const location = useLocation();
  const label = routeLabels[location.pathname]
    ?? (location.pathname.startsWith("/experimental/") && location.pathname !== "/experimental/compare"
      ? "Detalle del Run"
      : "Página");
  return (
    <header className="h-16 shrink-0 border-b border-border flex items-center justify-between px-6">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">GEO-Audit</span>
        <span className="text-muted-foreground">/</span>
        <span className="text-foreground font-medium">{label}</span>
      </div>
    </header>
  );
}
