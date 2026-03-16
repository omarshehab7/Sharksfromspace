/**
 * useHotspots.ts
 * Fetches shark activity hotspots from the backend API.
 * Falls back to demo data when the API is unreachable.
 */

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../services/apiClient";

export interface Hotspot {
  id: string;
  latitude: number;
  longitude: number;
  risk_level: "low" | "medium" | "high";
  species: string[];
  sst: number;
  chlorophyll: number;
  front_intensity: number;
  eddy_proximity: number;
  probability_of_shark_activity: number;
}

interface LocationState {
  latitude: number;
  longitude: number;
}

async function fetchHotspots(location: LocationState | null): Promise<Hotspot[]> {
  const params = location
    ? {
        lat: location.latitude,
        lon: location.longitude,
        radius_km: 1000,
      }
    : { lat: 27.0, lon: -76.5, radius_km: 2000 };

  const response = await apiClient.get("/api/predictions/hotspots", { params });
  return response.data.hotspots;
}

export function useHotspots(location: LocationState | null) {
  return useQuery<Hotspot[]>({
    queryKey: ["hotspots", location?.latitude, location?.longitude],
    queryFn: () => fetchHotspots(location),
    refetchInterval: 5 * 60 * 1000, // Poll every 5 min
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
