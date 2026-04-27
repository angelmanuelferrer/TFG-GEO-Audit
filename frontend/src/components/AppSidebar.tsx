import { NavLink as RouterNavLink, useLocation } from "react-router-dom";
import {
  Home,
  FlaskConical,
  GitCompare,
  Radio,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navGroups = [
  {
    label: "Análisis",
    items: [
      { to: "/", label: "Overview", icon: Home },
      { to: "/experimental", label: "Experimental", icon: FlaskConical },
      { to: "/experimental/compare", label: "Comparar Runs", icon: GitCompare },
      { to: "/live", label: "Live Multi-motor", icon: Radio },
      { to: "/seo", label: "SEO Histórico", icon: BarChart3 },
    ],
  },
];

export function AppSidebar() {
  const location = useLocation();

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 flex flex-col bg-sidebar border-r border-sidebar-border">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">G</span>
          </div>
          <div>
            <h1 className="text-foreground font-semibold text-base leading-tight">GEO-Audit</h1>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent text-muted-foreground font-medium">
              programamos.es
            </span>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {navGroups.map((group) => (
          <div key={group.label}>
            <p className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold px-3 mb-2">
              {group.label}
            </p>
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const isActive =
                  item.to === "/"
                    ? location.pathname === "/"
                    : location.pathname.startsWith(item.to);
                return (
                  <li key={item.to}>
                    <RouterNavLink
                      to={item.to}
                      className={cn(
                        "flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors",
                        isActive
                          ? "bg-primary/10 text-primary font-medium"
                          : "text-muted-foreground hover:text-foreground hover:bg-accent"
                      )}
                    >
                      <item.icon className="h-4 w-4 shrink-0" />
                      <span>{item.label}</span>
                    </RouterNavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

    </aside>
  );
}
