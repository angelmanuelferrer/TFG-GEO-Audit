import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { DashboardLayout } from "@/components/DashboardLayout";
import Index from "./pages/Index";
import ExperimentalPage from "./pages/Experimental";
import RunDetailPage from "./pages/RunDetail";
import ComparePage from "./pages/Compare";
import LivePage from "./pages/Live";
import SeoPage from "./pages/Seo";
import OptimizerPage from "./pages/Optimizer";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Index />} />
            <Route path="/experimental" element={<ExperimentalPage />} />
            <Route path="/experimental/compare" element={<ComparePage />} />
            <Route path="/experimental/:runId" element={<RunDetailPage />} />
            <Route path="/live" element={<LivePage />} />
            <Route path="/seo" element={<SeoPage />} />
            <Route path="/optimizer" element={<OptimizerPage />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
