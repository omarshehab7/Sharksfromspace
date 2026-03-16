/**
 * HomeScreen.tsx — Interactive Ocean Map
 *
 * Full-screen map with:
 *  - Shark activity hotspot markers (color-coded by risk)
 *  - Ocean layer toggles (SST heatmap, productivity, currents)
 *  - Bottom sheet with quick hotspot info
 *  - Layer toggle toolbar
 */

import React, { useState, useCallback, useRef } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Animated,
  StyleSheet,
  Platform,
} from "react-native";
import MapboxGL from "@rnmapbox/maps";
import { useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useHotspots } from "../hooks/useHotspots";
import { useLocation } from "../hooks/useLocation";

// ---- Types ----
interface Hotspot {
  id: string;
  latitude: number;
  longitude: number;
  risk_level: "low" | "medium" | "high";
  species: string[];
  sst: number;
  chlorophyll: number;
  front_intensity: number;
  eddy_proximity: number;
}

// ---- Constants ----
const RISK_COLORS = {
  low: "#22C55E",
  medium: "#F59E0B",
  high: "#EF4444",
};

const RISK_LABELS = {
  low: "Low Activity",
  medium: "Moderate Activity",
  high: "High Activity",
};

const OCEAN_LAYERS = [
  { id: "sst", label: "🌡️ Temperature", color: "#F87171" },
  { id: "productivity", label: "🟢 Productivity", color: "#4ADE80" },
  { id: "currents", label: "🌊 Currents", color: "#60A5FA" },
];

// ---- Simulated hotspot data (fallback when API unavailable) ----
const DEMO_HOTSPOTS: Hotspot[] = [
  { id: "h1", latitude: 27.5, longitude: -79.5, risk_level: "high", species: ["Great White Shark", "Hammerhead Shark"], sst: 26.2, chlorophyll: 2.1, front_intensity: 0.82, eddy_proximity: 0.71 },
  { id: "h2", latitude: 25.2, longitude: -74.8, risk_level: "medium", species: ["Tiger Shark", "Bull Shark"], sst: 28.7, chlorophyll: 1.3, front_intensity: 0.54, eddy_proximity: 0.45 },
  { id: "h3", latitude: 30.1, longitude: -77.3, risk_level: "high", species: ["Mako Shark", "Blue Shark"], sst: 23.1, chlorophyll: 3.4, front_intensity: 0.91, eddy_proximity: 0.88 },
  { id: "h4", latitude: 22.8, longitude: -82.1, risk_level: "medium", species: ["Whale Shark"], sst: 30.1, chlorophyll: 0.8, front_intensity: 0.31, eddy_proximity: 0.29 },
  { id: "h5", latitude: 33.4, longitude: -76.2, risk_level: "low", species: ["Blue Shark"], sst: 19.8, chlorophyll: 1.1, front_intensity: 0.22, eddy_proximity: 0.15 },
];

// ---- Main Component ----
export default function HomeScreen() {
  const navigation = useNavigation<any>();
  const insets = useSafeAreaInsets();
  const { location } = useLocation();
  const { data: apiHotspots, isLoading } = useHotspots(location);

  const hotspots: Hotspot[] = apiHotspots ?? DEMO_HOTSPOTS;

  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);
  const [activeLayers, setActiveLayers] = useState<Set<string>>(new Set(["sst"]));
  const [showLayerPanel, setShowLayerPanel] = useState(false);
  const sheetAnim = useRef(new Animated.Value(0)).current;

  const toggleLayer = useCallback((id: string) => {
    setActiveLayers((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }, []);

  const handleMarkerPress = useCallback((hotspot: Hotspot) => {
    setSelectedHotspot(hotspot);
    Animated.spring(sheetAnim, { toValue: 1, useNativeDriver: true, tension: 80 }).start();
  }, [sheetAnim]);

  const handleDismiss = useCallback(() => {
    Animated.timing(sheetAnim, { toValue: 0, duration: 200, useNativeDriver: true }).start(() =>
      setSelectedHotspot(null)
    );
  }, [sheetAnim]);

  const handleDetailPress = useCallback(() => {
    if (selectedHotspot) {
      navigation.navigate("HotspotDetail", { hotspot: selectedHotspot });
    }
  }, [selectedHotspot, navigation]);

  const sheetTranslate = sheetAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [200, 0],
  });

  return (
    <View style={styles.container}>
      {/* ---- Map ---- */}
      <MapboxGL.MapView
        style={styles.map}
        styleURL={MapboxGL.StyleURL.Dark}
        logoEnabled={false}
        compassEnabled
        compassViewPosition={0}
      >
        <MapboxGL.Camera
          zoomLevel={5}
          centerCoordinate={
            // If using real API data AND real location, center on user
            // Otherwise, always center on the demo hotspot area (Atlantic)
            apiHotspots && location
              ? [location.longitude, location.latitude]
              : [-76.5, 27.0]
          }
          animationDuration={800}
        />
        <MapboxGL.UserLocation visible />

        {/* Hotspot Markers */}
        {hotspots.map((h) => (
          <MapboxGL.MarkerView key={h.id} coordinate={[h.longitude, h.latitude]}>
            <TouchableOpacity onPress={() => handleMarkerPress(h)} activeOpacity={0.85}>
              <View style={[styles.markerOuter, { borderColor: RISK_COLORS[h.risk_level] }]}>
                <View style={[styles.markerInner, { backgroundColor: RISK_COLORS[h.risk_level] }]}>
                  <Text style={styles.markerText}>🦈</Text>
                </View>
              </View>
              {/* Pulse ring for high risk */}
              {h.risk_level === "high" && (
                <View style={[styles.markerPulse, { borderColor: RISK_COLORS.high }]} />
              )}
            </TouchableOpacity>
          </MapboxGL.MarkerView>
        ))}
      </MapboxGL.MapView>

      {/* ---- Top Header Bar ---- */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <View>
          <Text style={styles.headerTitle}>🦈 Sharks From Space</Text>
          <Text style={styles.headerSub}>{hotspots.length} hotspots detected</Text>
        </View>
        <TouchableOpacity
          style={styles.layerBtn}
          onPress={() => setShowLayerPanel((v) => !v)}
        >
          <Ionicons name="layers-outline" size={20} color="#CEE9F7" />
        </TouchableOpacity>
      </View>

      {/* ---- Layer Toggle Panel ---- */}
      {showLayerPanel && (
        <View style={[styles.layerPanel, { top: insets.top + 72 }]}>
          <Text style={styles.layerPanelTitle}>Map Layers</Text>
          {OCEAN_LAYERS.map((layer) => {
            const active = activeLayers.has(layer.id);
            return (
              <TouchableOpacity
                key={layer.id}
                style={[styles.layerToggle, active && { backgroundColor: "#0A2540" }]}
                onPress={() => toggleLayer(layer.id)}
              >
                <Text style={styles.layerLabel}>{layer.label}</Text>
                <View
                  style={[
                    styles.layerIndicator,
                    { backgroundColor: active ? layer.color : "#1C3A52" },
                  ]}
                />
              </TouchableOpacity>
            );
          })}
        </View>
      )}

      {/* ---- Risk Legend ---- */}
      <View style={styles.legend}>
        {(Object.keys(RISK_COLORS) as Array<keyof typeof RISK_COLORS>).map((level) => (
          <View key={level} style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: RISK_COLORS[level] }]} />
            <Text style={styles.legendText}>{level.charAt(0).toUpperCase() + level.slice(1)}</Text>
          </View>
        ))}
      </View>

      {/* ---- Bottom Sheet (selected hotspot) ---- */}
      {selectedHotspot && (
        <Animated.View
          style={[
            styles.sheet,
            { transform: [{ translateY: sheetTranslate }] },
          ]}
        >
          {/* Drag handle */}
          <View style={styles.sheetHandle} />

          {/* Dismiss */}
          <TouchableOpacity style={styles.sheetClose} onPress={handleDismiss}>
            <Ionicons name="close" size={18} color="#8AB9CE" />
          </TouchableOpacity>

          {/* Risk banner */}
          <View style={[styles.riskBanner, { backgroundColor: RISK_COLORS[selectedHotspot.risk_level] + "22", borderColor: RISK_COLORS[selectedHotspot.risk_level] }]}>
            <View style={[styles.riskDot, { backgroundColor: RISK_COLORS[selectedHotspot.risk_level] }]} />
            <Text style={[styles.riskLabel, { color: RISK_COLORS[selectedHotspot.risk_level] }]}>
              {RISK_LABELS[selectedHotspot.risk_level]}
            </Text>
          </View>

          {/* Quick stats row */}
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>🌡️</Text>
              <Text style={styles.statValue}>{selectedHotspot.sst.toFixed(1)}°C</Text>
              <Text style={styles.statLabel}>Temperature</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>🟢</Text>
              <Text style={styles.statValue}>{selectedHotspot.chlorophyll.toFixed(1)}</Text>
              <Text style={styles.statLabel}>Chlorophyll</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>🌀</Text>
              <Text style={styles.statValue}>{Math.round(selectedHotspot.eddy_proximity * 100)}%</Text>
              <Text style={styles.statLabel}>Eddy Zone</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statIcon}>〰</Text>
              <Text style={styles.statValue}>{Math.round(selectedHotspot.front_intensity * 100)}%</Text>
              <Text style={styles.statLabel}>Front</Text>
            </View>
          </View>

          {/* Species chips */}
          {selectedHotspot.species.length > 0 && (
            <View style={styles.speciesRow}>
              {selectedHotspot.species.slice(0, 3).map((s) => (
                <View key={s} style={styles.speciesChip}>
                  <Text style={styles.speciesChipText}>🦈 {s}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Details button */}
          <TouchableOpacity style={styles.detailsBtn} onPress={handleDetailPress}>
            <Text style={styles.detailsBtnText}>See Full Details</Text>
            <Ionicons name="arrow-forward" size={16} color="#050D1A" />
          </TouchableOpacity>
        </Animated.View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#050D1A" },
  map: { flex: 1 },

  // Header
  header: {
    position: "absolute",
    top: 0, left: 0, right: 0,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: "rgba(5,13,26,0.85)",
  },
  headerTitle: { color: "#CEE9F7", fontSize: 18, fontWeight: "800" },
  headerSub: { color: "#4A7FA5", fontSize: 12, marginTop: 2 },
  layerBtn: {
    width: 40, height: 40,
    borderRadius: 20,
    backgroundColor: "#0A2540",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#1C3A52",
  },

  // Layer panel
  layerPanel: {
    position: "absolute",
    right: 16,
    backgroundColor: "#050D1A",
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: "#0A2540",
    minWidth: 195,
  },
  layerPanelTitle: { color: "#8AB9CE", fontSize: 12, fontWeight: "700", marginBottom: 10, letterSpacing: 0.8 },
  layerToggle: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderRadius: 8,
    marginBottom: 4,
  },
  layerLabel: { color: "#CEE9F7", fontSize: 13 },
  layerIndicator: { width: 12, height: 12, borderRadius: 6 },

  // Legend
  legend: {
    position: "absolute",
    bottom: 180,
    left: 16,
    backgroundColor: "rgba(5,13,26,0.80)",
    borderRadius: 12,
    padding: 10,
    gap: 6,
    borderWidth: 1,
    borderColor: "#0A2540",
  },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 8 },
  legendDot: { width: 10, height: 10, borderRadius: 5 },
  legendText: { color: "#8AB9CE", fontSize: 12 },

  // Markers
  markerOuter: {
    width: 42, height: 42,
    borderRadius: 21,
    borderWidth: 2.5,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(5,13,26,0.7)",
  },
  markerInner: {
    width: 28, height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  markerText: { fontSize: 14 },
  markerPulse: {
    position: "absolute",
    width: 56, height: 56,
    borderRadius: 28,
    borderWidth: 2,
    opacity: 0.4,
    top: -7, left: -7,
  },

  // Bottom sheet
  sheet: {
    position: "absolute",
    bottom: 0, left: 0, right: 0,
    backgroundColor: "#071525",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    paddingBottom: 34,
    borderTopWidth: 1,
    borderColor: "#0A2540",
  },
  sheetHandle: {
    width: 40, height: 4,
    borderRadius: 2,
    backgroundColor: "#1C3A52",
    alignSelf: "center",
    marginBottom: 14,
  },
  sheetClose: {
    position: "absolute",
    top: 20, right: 20,
    width: 30, height: 30,
    alignItems: "center",
    justifyContent: "center",
  },
  riskBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginBottom: 16,
  },
  riskDot: { width: 10, height: 10, borderRadius: 5 },
  riskLabel: { fontWeight: "700", fontSize: 14 },

  statsRow: {
    flexDirection: "row",
    justifyContent: "space-around",
    marginBottom: 16,
    backgroundColor: "#0A1D30",
    borderRadius: 14,
    paddingVertical: 14,
  },
  statItem: { alignItems: "center", flex: 1 },
  statIcon: { fontSize: 18, marginBottom: 4 },
  statValue: { color: "#CEE9F7", fontSize: 15, fontWeight: "700" },
  statLabel: { color: "#4A7FA5", fontSize: 10, marginTop: 2 },
  statDivider: { width: 1, backgroundColor: "#0A2540" },

  speciesRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 14 },
  speciesChip: {
    backgroundColor: "#0A2540",
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: "#1C3A52",
  },
  speciesChipText: { color: "#8AC8E5", fontSize: 12 },

  detailsBtn: {
    backgroundColor: "#29ABE2",
    borderRadius: 14,
    paddingVertical: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  detailsBtnText: { color: "#050D1A", fontWeight: "800", fontSize: 16 },
});
