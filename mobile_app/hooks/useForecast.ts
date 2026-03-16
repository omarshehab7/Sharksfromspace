/**
 * hooks/useForecast.ts  — GET /api/forecast
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../services/apiClient";

export interface ForecastDay {
  date: string;
  day_label: string;
  risk_level: "low" | "medium" | "high";
  risk_score: number;
  predicted_sst: number;
  predicted_chlorophyll: number;
  predicted_front_intensity: number;
  confidence: number;
  likely_species: string[];
}

interface ForecastResponse {
  latitude: number;
  longitude: number;
  days: ForecastDay[];
  generated_at: string;
}

async function fetchForecast(lat: number, lon: number, days = 7): Promise<ForecastResponse> {
  const res = await apiClient.get("/api/forecast", { params: { lat, lon, days } });
  return res.data;
}

export function useForecast(lat: number | null, lon: number | null, days = 7) {
  return useQuery<ForecastResponse>({
    queryKey: ["forecast", lat, lon, days],
    queryFn: () => fetchForecast(lat!, lon!, days),
    enabled: lat !== null && lon !== null,
    staleTime: 30 * 60 * 1000, // 30 min — forecasts don't change often
    retry: 1,
  });
}
