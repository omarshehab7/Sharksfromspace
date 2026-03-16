/**
 * oceanCurrents.ts — Ocean Current Vector Overlay Configuration
 *
 * Defines the Mapbox line layer style for visualizing ocean currents
 * on the map. Currents are displayed as animated directional lines
 * that vary in width and color based on speed.
 */

export const oceanCurrentLayerStyle = {
  // Line color based on current speed (m/s)
  lineColor: [
    "interpolate",
    ["linear"],
    ["get", "speed"],
    0,   "#073449",   // Slow: dark blue
    0.5, "#2E9DCD",   // Moderate: blue
    1.0, "#5AB5D9",   // Fast: light blue
    2.0, "#E6F4F9",   // Very fast: white
  ],

  // Line width based on current speed
  lineWidth: [
    "interpolate",
    ["linear"],
    ["get", "speed"],
    0,   1,
    1.0, 3,
    2.0, 5,
  ],

  lineOpacity: 0.6,

  // Line cap style for smooth rendering
  lineCap: "round" as const,
  lineJoin: "round" as const,
};

/**
 * Configuration for the ocean current data source.
 * The backend provides GeoJSON LineString features representing
 * current vectors with speed and direction properties.
 */
export const oceanCurrentSourceConfig = {
  type: "geojson" as const,
  data: {
    type: "FeatureCollection" as const,
    features: [], // Populated dynamically from API
  },
};
