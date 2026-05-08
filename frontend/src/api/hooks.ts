import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import apiClient from "./client";
import type {
  OverviewResponse, RunsListResponse, RunScorecard, RawResponse, CompareResponse,
  LiveRunsListResponse, LiveRunResponse, CoverageMatrixResponse, SentimentDistribution,
  SeoSnapshot, Job, JobsListResponse, LaunchJobRequest,
} from "./types";

export function useOverview() {
  return useQuery<OverviewResponse>({
    queryKey: ["overview"],
    queryFn: async () => {
      const { data } = await apiClient.get<OverviewResponse>("/api/dashboard/overview");
      return data;
    },
    staleTime: 60_000,
  });
}

export function useExperimentalRuns() {
  return useQuery<RunsListResponse>({
    queryKey: ["experimental-runs"],
    queryFn: async () => {
      const { data } = await apiClient.get<RunsListResponse>("/api/runs/experimental");
      return data;
    },
    staleTime: 60_000,
  });
}

export function useRunScorecard(runId: string | undefined) {
  return useQuery<RunScorecard>({
    queryKey: ["run-scorecard", runId],
    queryFn: async () => {
      const { data } = await apiClient.get<RunScorecard>(`/api/runs/experimental/${runId}`);
      return data;
    },
    enabled: !!runId,
    staleTime: 60_000,
  });
}

export function useRunRaw(runId: string | undefined) {
  return useQuery<RawResponse>({
    queryKey: ["run-raw", runId],
    queryFn: async () => {
      const { data } = await apiClient.get<RawResponse>(`/api/runs/experimental/${runId}/raw`, { params: { limit: 200 } });
      return data;
    },
    enabled: !!runId,
    staleTime: 60_000,
  });
}

export function useCompareRuns(runA: string, runB: string, enabled: boolean) {
  return useQuery<CompareResponse>({
    queryKey: ["compare-runs", runA, runB],
    queryFn: async () => {
      const { data } = await apiClient.get<CompareResponse>("/api/runs/experimental/compare", { params: { a: runA, b: runB } });
      return data;
    },
    enabled,
    staleTime: 60_000,
  });
}

export function useLiveRunsList() {
  return useQuery<LiveRunsListResponse>({
    queryKey: ["live-runs"],
    queryFn: async () => {
      const { data } = await apiClient.get<LiveRunsListResponse>("/api/runs/live");
      return data;
    },
    staleTime: 60_000,
  });
}

export function useLiveRun(runId: string) {
  return useQuery<LiveRunResponse>({
    queryKey: ["live-run", runId],
    queryFn: async () => {
      const endpoint = runId === "latest" ? "/api/runs/live/latest" : `/api/runs/live/${runId}`;
      const { data } = await apiClient.get<LiveRunResponse>(endpoint);
      return data;
    },
    staleTime: 60_000,
  });
}

export function useCoverageMatrix(runId: string) {
  return useQuery<CoverageMatrixResponse>({
    queryKey: ["coverage-matrix", runId],
    queryFn: async () => {
      const { data } = await apiClient.get<CoverageMatrixResponse>("/api/metrics/coverage-matrix", { params: { run_id: runId } });
      return data;
    },
    staleTime: 60_000,
  });
}

export function useSentimentDistribution(runId: string) {
  return useQuery<SentimentDistribution[]>({
    queryKey: ["sentiment", runId],
    queryFn: async () => {
      const { data } = await apiClient.get<SentimentDistribution[]>("/api/metrics/sentiment-distribution", { params: { run_id: runId } });
      return data;
    },
    staleTime: 60_000,
  });
}

// === SEO hooks ===

export function useSeoLatest() {
  return useQuery<SeoSnapshot>({
    queryKey: ["seo-latest"],
    queryFn: async () => {
      const { data } = await apiClient.get<SeoSnapshot>("/api/seo/latest");
      return data;
    },
    staleTime: 60_000,
  });
}

export function useSeoHistory() {
  return useQuery<SeoSnapshot[]>({
    queryKey: ["seo-history"],
    queryFn: async () => {
      const { data } = await apiClient.get<SeoSnapshot[]>("/api/seo/history", { params: { device: "both" } });
      return data;
    },
    staleTime: 60_000,
  });
}

// === Jobs hooks ===

export function useJobs(hasRunning: boolean) {
  return useQuery<JobsListResponse>({
    queryKey: ["jobs"],
    queryFn: async () => {
      const { data } = await apiClient.get<JobsListResponse>("/api/jobs");
      return data;
    },
    // Refresca cada 4s si hay un job activo, cada 30s si no
    refetchInterval: hasRunning ? 4_000 : 30_000,
    staleTime: 0,
  });
}

export function useJob(jobId: string | undefined) {
  return useQuery<Job>({
    queryKey: ["job", jobId],
    queryFn: async () => {
      const { data } = await apiClient.get<Job>(`/api/jobs/${jobId}`);
      return data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "running" ? 3_000 : false;
    },
    staleTime: 0,
  });
}

export function useLaunchJob() {
  const qc = useQueryClient();
  return useMutation<Job, Error, LaunchJobRequest>({
    mutationFn: async (body) => {
      const { data } = await apiClient.post<Job>("/api/jobs", body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

