/**
 * useLocation.ts
 * Requests and tracks the user's current GPS location.
 */

import { useState, useEffect } from "react";
import * as ExpoLocation from "expo-location";

interface LocationState {
  latitude: number;
  longitude: number;
}

export function useLocation() {
  const [location, setLocation] = useState<LocationState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function getLocation() {
      try {
        const { status } = await ExpoLocation.requestForegroundPermissionsAsync();
        if (status !== "granted") {
          if (mounted) { setError("Location permission denied"); setLoading(false); }
          return;
        }

        const loc = await ExpoLocation.getCurrentPositionAsync({
          accuracy: ExpoLocation.Accuracy.Balanced,
        });

        if (mounted) {
          setLocation({ latitude: loc.coords.latitude, longitude: loc.coords.longitude });
          setLoading(false);
        }
      } catch (e) {
        if (mounted) { setError("Unable to get location"); setLoading(false); }
      }
    }

    getLocation();
    return () => { mounted = false; };
  }, []);

  return { location, loading, error };
}
