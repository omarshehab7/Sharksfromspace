/**
 * hooks/usePredictions.ts  — GET /api/predict
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../services/apiClient";
import type { Hotspot } from "./useHotspots";

interface PredictionParams {
  lat: number;
  lon: number;
  radius_km?: number;
  risk_level?: "low" | "medium" | "high";
  limit?: number;
}

interface PredictResponse {
  hotspots: Hotspot[];
  total: number;
  last_updated: string;
  model_version: string;
  data_sources: string[];
}

async function fetchPredictions(params: PredictionParams): Promise<PredictResponse> {
  const res = await apiClient.get("/api/predict", { params });
  return res.data;
}

export function usePredictions(params: PredictionParams) {
  return useQuery<PredictResponse>({
    queryKey: ["predictions", params.lat, params.lon, params.radius_km, params.risk_level],
    queryFn: () => fetchPredictions(params),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: !!params.lat && !!params.lon,
  });
}
