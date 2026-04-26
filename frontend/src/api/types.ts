export interface RunSummary {
  run_id: string;
  timestamp: string;
  rotation_block: string | null;
  n_queries: number;
  n_successful: number;
  n_errors: number;
  visibility_rate: number;
  avg_som: number;
  avg_citations: number;
}

export interface EngineStats {
  visibility_rate: number;
  avg_som: number;
  avg_first_rank: number | null;
  n_visible: number;
  n_queries: number;
}

export interface OverviewResponse {
  target: { url: string; brand: string };
  experimental: (RunSummary & {
    delta_vs_previous: {
      visibility_rate: number | null;
      avg_som: number | null;
      avg_citations: number | null;
    } | null;
  }) | null;
  live: {
    latest_run_id: string;
    timestamp: string;
    engine_coverage_avg: number;
    by_engine: Record<string, EngineStats>;
  } | null;
  seo: {
    fecha: string;
    mobile: { performance: number; seo: number; accessibility: number; lcp: string };
    desktop: { performance: number; seo: number; accessibility: number };
  } | null;
  alerts: string[];
}

export interface RunsListResponse {
  items: RunSummary[];
  total: number;
}

export interface BrandMention {
  source: string;
  position: number;
  context: string;
}

export interface PerQueryMetric {
  query_id: string;
  query: string;
  category: string;
  total_citations: number;
  target_citations: number;
  is_visible: boolean;
  som: number;
  first_citation_rank: number | null;
  pawc: number;
  citation_rate: number;
  brand_mentions: BrandMention[];
  error?: string;
}

export interface CategoryStats {
  n: number;
  n_errors: number;
  n_successful: number;
  visibility_rate: number;
  avg_som: number;
  avg_citations: number;
}

export interface RunScorecard extends RunSummary {
  by_category: Record<string, CategoryStats>;
  per_query_metrics: PerQueryMetric[];
  _derived: {
    avg_first_rank_by_category: Record<string, number>;
    avg_pawc_by_category: Record<string, number>;
  };
}

export interface RawResponseItem {
  query_id: string;
  query: string;
  answer?: {
    answer: string;
    citations: { index: number; url: string; quote: string }[];
    sources_used: string[];
    sources_available_but_unused: string[];
  };
  error?: string;
}

export interface RawResponse {
  items: RawResponseItem[];
  total: number;
}

export interface SomShift {
  query_id: string;
  from_som: number;
  to_som: number;
  delta: number;
}

export interface RankingShift {
  query_id: string;
  from_rank: number;
  to_rank: number;
}

export interface CompareResponse {
  run_a: string;
  run_b: string;
  deltas: {
    visibility_rate: number;
    avg_som: number;
    avg_citations: number;
  };
  queries_gained: string[];
  queries_lost: string[];
  queries_stable_visible: string[];
  ranking_shifts: RankingShift[];
  som_shifts: SomShift[];
}

// === Live types ===

export interface LiveEngineSummary {
  visibility_rate: number;
  avg_som: number;
  avg_first_rank: number | null;
  n_queries: number;
  n_visible: number;
}

export interface LiveBrandMention {
  source: string;
  position: number;
  context: string;
}

export interface LiveEngineResult {
  total_citations: number;
  target_citations: number;
  is_visible: boolean;
  som: number;
  first_citation_rank: number | null;
  brand_mentions: LiveBrandMention[];
  sentiment: string | null;
}

export interface LiveQueryResult {
  query_id: string;
  query_text: string;
  query_category: string;
  engine_coverage: number;
  engines: Record<string, LiveEngineResult>;
}

export interface LiveRunResponse {
  run_id: string;
  timestamp: string;
  engines: string[];
  n_queries: number;
  engine_coverage_avg: number;
  summary: Record<string, LiveEngineSummary>;
  results: LiveQueryResult[];
}

export interface LiveRunListItem {
  run_id: string;
  timestamp: string;
  engines: string[];
  n_queries: number;
}

export interface LiveRunsListResponse {
  items: LiveRunListItem[];
  total: number;
}

export interface CoverageMatrixResponse {
  categories: string[];
  engines: string[];
  matrix: Record<string, Record<string, number>>;
}

export interface SentimentDistribution {
  engine: string;
  POSITIVO: number;
  NEUTRO: number;
  NEGATIVO: number;
  null: number;
}

// === SEO types ===

export interface SeoMobileMetrics {
  performance: number;
  seo: number;
  accessibility: number;
  lcp: string;
  tbt: string;
}

export interface SeoDesktopMetrics {
  performance: number;
  seo: number;
  accessibility: number;
}

export interface SeoSnapshot {
  fecha: string;
  mobile: SeoMobileMetrics;
  desktop: SeoDesktopMetrics;
}

// === Timeline types ===

export interface TimelinePoint {
  run_id: string;
  timestamp: string;
  value: number;
}

export interface TimelineResponse {
  metric: string;
  source: string;
  engine?: string;
  device?: string;
  points: TimelinePoint[];
}

// === Queries types ===

export interface QueryCatalogItem {
  query_id: string;
  query: string;
  category: string;
  block: string;
  original_15: boolean;
}

export interface QueryDetail extends QueryCatalogItem {
  experimental_runs: { run_id: string; is_visible: boolean; som: number; first_citation_rank: number | null }[];
  live_visibility_avg: number | null;
  total_experimental_runs: number;
  visible_in_runs: number;
}

export interface QueriesCatalogResponse {
  items: QueryCatalogItem[];
  total: number;
}

// === Jobs types ===

export type JobStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

export interface ScriptInfo {
  script_id: string;
  name: string;
  description: string;
  side_effects: string;
  cost_estimate: string;
  duration_estimate: string;
  env_vars: string[];
  requires_confirmation: boolean;
  args_schema?: {
    block?: { type: "select"; options: string[] };
    engines?: { type: "multi-select"; options: string[] };
    tier?: { type: "select"; options: string[] };
  };
}

export interface ScriptsResponse {
  scripts: ScriptInfo[];
}

export interface JobPreview {
  script_id: string;
  cost_estimate: string;
  duration_estimate: string;
  side_effects: string;
  missing_env: string[];
  available_env: string[];
}

export interface Job {
  id: string;
  script_id: string;
  script_name: string;
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  output_path: string | null;
  error: string | null;
  args: Record<string, unknown>;
}

export interface JobsListResponse {
  items: Job[];
  total: number;
}

export interface JobLogs {
  job_id: string;
  lines: string[];
}
