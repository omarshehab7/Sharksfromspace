/**
 * hotspotClusters.ts — Cluster Layer Configuration
 *
 * Defines Mapbox clustering behavior for shark hotspot markers.
 * When many hotspots are close together, they're grouped into
 * clusters with a count badge. Clusters expand on zoom.
 */

export const clusterProperties = {
  // Group hotspots within 50px radius
  clusterRadius: 50,
  clusterMaxZoom: 14,

  // Cluster paint style
  clusterPaint: {
    // Circle color scales with cluster size
    "circle-color": [
      "step",
      ["get", "point_count"],
      "#2E9DCD",   // < 10 hotspots: blue
      10,
      "#FF6B35",   // 10-25 hotspots: orange
      25,
      "#E63946",   // 25+ hotspots: red
    ],

    // Circle radius scales with cluster size
    "circle-radius": [
      "step",
      ["get", "point_count"],
      20,   // < 10
      10,
      30,   // 10-25
      25,
      40,   // 25+
    ],

    "circle-opacity": 0.85,
    "circle-stroke-width": 2,
    "circle-stroke-color": "#0A1628",
  },

  // Cluster count text style
  clusterTextLayout: {
    "text-field": ["get", "point_count_abbreviated"],
    "text-size": 14,
  },

  clusterTextPaint: {
    "text-color": "#E6F4F9",
  },
};
