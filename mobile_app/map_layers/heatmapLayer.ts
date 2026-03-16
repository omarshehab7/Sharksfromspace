/**
 * heatmapLayer.ts — Mapbox heatmap style configuration
 *
 * Used by HomeScreen to render a shark activity heatmap
 * from GeoJSON prediction data as a Mapbox layer.
 */

import MapboxGL from "@rnmapbox/maps";

export const heatmapLayerStyle: MapboxGL.HeatmapLayerStyle = {
  heatmapWeight: [
    "interpolate",
    ["linear"],
    ["get", "probability_of_shark_activity"],
    0, 0,
    1, 1,
  ],
  heatmapIntensity: [
    "interpolate",
    ["linear"],
    ["zoom"],
    4, 0.5,
    10, 2.0,
  ],
  heatmapColor: [
    "interpolate",
    ["linear"],
    ["heatmap-density"],
    0,   "rgba(0, 0, 255, 0)",
    0.2, "rgba(0, 150, 200, 0.4)",
    0.4, "rgba(34, 197, 94, 0.6)",
    0.6, "rgba(245, 158, 11, 0.7)",
    0.8, "rgba(239, 68, 68, 0.85)",
    1.0, "rgba(255, 30, 30, 1)",
  ],
  heatmapRadius: [
    "interpolate",
    ["linear"],
    ["zoom"],
    4, 30,
    8, 60,
  ],
  heatmapOpacity: [
    "interpolate",
    ["linear"],
    ["zoom"],
    4, 0.75,
    10, 0.5,
  ],
};

/** Circle layer style for individual prediction points */
export const predictionPointStyle: MapboxGL.CircleLayerStyle = {
  circleRadius: [
    "interpolate",
    ["linear"],
    ["zoom"],
    5, 4,
    10, 10,
  ],
  circleColor: [
    "match",
    ["get", "risk_level"],
    "high",   "#EF4444",
    "medium", "#F59E0B",
    "low",    "#22C55E",
    "#8AB9CE",
  ],
  circleOpacity: 0.9,
  circlePitchAlignment: "map",
};
