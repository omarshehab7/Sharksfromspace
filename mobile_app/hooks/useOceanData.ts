/**
 * useOceanData.ts
 * Fetches supplemental ocean data (depth, current speed) for a lat/lon.
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../services/apiClient";

interface OceanData {
  depth: number | null;
  current_speed: number | null;
  current_direction: string | null;
}

async function fetchOceanData(lat: number, lon: number): Promise<OceanData> {
  const response = await apiClient.get("/api/ocean-data", { params: { lat, lon } });
  return response.data;
}

export function useOceanData(lat: number, lon: number) {
  return useQuery<OceanData>({
    queryKey: ["oceanData", lat, lon],
    queryFn: () => fetchOceanData(lat, lon),
    staleTime: 15 * 60 * 1000, // 15 min
    retry: 1,
  });
}
