/**
 * HotspotDetailScreen.tsx — Hotspot Deep-Dive
 *
 * Shows a full, plain-language explanation of why a location is a hotspot.
 * Simple, visual, non-scientific language throughout.
 */

import React from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
} from "react-native";
import { useRoute, useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";

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
const RISK_COLORS = { low: "#22C55E", medium: "#F59E0B", high: "#EF4444" };
const RISK_BG = { low: "#052010", medium: "#1E1000", high: "#1E0505" };

const SPECIES_FACTS: Record<string, { emoji: string; diet: string; size: string; fact: string }> = {
  "Great White Shark": { emoji: "🦈", diet: "Seals, sea lions, tuna", size: "Up to 6m (20 ft)", fact: "Can detect blood from up to 5km away" },
  "Tiger Shark": { emoji: "🦈", diet: "Fish, sea turtles, rays", size: "Up to 5.5m (18 ft)", fact: "Known as the 'ocean garbage can' — eats almost anything" },
  "Hammerhead Shark": { emoji: "🦈", diet: "Rays, squid, fish", size: "Up to 4m (13 ft)", fact: "Their wide head gives them 360° vision" },
  "Bull Shark": { emoji: "🦈", diet: "Fish, dolphins, rays", size: "Up to 3.4m (11 ft)", fact: "Can survive in freshwater rivers" },
  "Whale Shark": { emoji: "🐋", diet: "Plankton, krill", size: "Up to 12m (40 ft)", fact: "Largest fish in the ocean — gentle giants!" },
  "Mako Shark": { emoji: "🦈", diet: "Tuna, billfish", size: "Up to 4m (13 ft)", fact: "The fastest shark — can reach 45 mph" },
  "Blue Shark": { emoji: "🦈", diet: "Squid, small fish", size: "Up to 3.8m (12.5 ft)", fact: "One of the most widely distributed sharks on Earth" },
};

// ---- Explanation builder ----
function buildExplanation(hotspot: Hotspot): string[] {
  const reasons: string[] = [];
  if (hotspot.sst >= 18 && hotspot.sst <= 30)
    reasons.push(`🌡️ The water temperature is ${hotspot.sst.toFixed(1)}°C — ideal for shark activity and the fish they hunt`);
  if (hotspot.chlorophyll > 1.0)
    reasons.push(`🟢 High plankton levels (${hotspot.chlorophyll.toFixed(1)} mg/m³) feed small fish, which attract larger predators`);
  if (hotspot.front_intensity > 0.5)
    reasons.push(`〰️ An ocean temperature boundary nearby concentrates prey fish — sharks often patrol these "edges"`);
  if (hotspot.eddy_proximity > 0.5)
    reasons.push(`🌀 A spinning ocean current (eddy) is trapping nutrients in this area — creating a feeding hotspot`);
  if (reasons.length === 0)
    reasons.push("🔍 Multiple ocean conditions combine to make this location worth watching");
  return reasons;
}

// ---- Component ----
export default function HotspotDetailScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { hotspot } = route.params as { hotspot: Hotspot };
  const reasons = buildExplanation(hotspot);

  const riskColor = RISK_COLORS[hotspot.risk_level];
  const riskBg = RISK_BG[hotspot.risk_level];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingBottom: 50 }}
      showsVerticalScrollIndicator={false}
    >
      {/* ---- Hero Risk Card ---- */}
      <View style={[styles.heroCard, { backgroundColor: riskBg, borderColor: riskColor }]}>
        <Text style={styles.heroEmoji}>🦈</Text>
        <Text style={styles.heroTitle}>Shark Activity Hotspot</Text>
        <View style={[styles.riskPill, { backgroundColor: riskColor }]}>
          <Text style={styles.riskPillText}>
            {hotspot.risk_level === "high" ? "⚠️ High Activity"
              : hotspot.risk_level === "medium" ? "🔶 Moderate Activity"
              : "✅ Low Activity"}
          </Text>
        </View>
        <Text style={styles.coordText}>
          {Math.abs(hotspot.latitude).toFixed(2)}°{hotspot.latitude >= 0 ? "N" : "S"},{"  "}
          {Math.abs(hotspot.longitude).toFixed(2)}°{hotspot.longitude <= 0 ? "W" : "E"}
        </Text>
      </View>

      {/* ---- Ocean Stats ---- */}
      <Text style={styles.sectionTitle}>🌊 Ocean Conditions</Text>
      <View style={styles.statsGrid}>
        <OceanStat icon="🌡️" label="Sea Temperature" value={`${hotspot.sst.toFixed(1)}°C`} note="Ideal range: 18–30°C" />
        <OceanStat icon="🟢" label="Plankton Level" value={`${hotspot.chlorophyll.toFixed(1)} mg/m³`} note={hotspot.chlorophyll > 1.5 ? "High — good feeding conditions" : "Moderate"} />
        <OceanStat icon="〰" label="Temperature Front" value={`${Math.round(hotspot.front_intensity * 100)}%`} note="How sharp the water boundary is" />
        <OceanStat icon="🌀" label="Eddy Influence" value={`${Math.round(hotspot.eddy_proximity * 100)}%`} note="Spinning current concentration" />
      </View>

      {/* ---- Why Here? ---- */}
      <Text style={styles.sectionTitle}>💡 Why sharks may be here</Text>
      <View style={styles.reasonsCard}>
        {reasons.map((r, i) => (
          <View key={i} style={[styles.reasonRow, i < reasons.length - 1 && styles.reasonBorder]}>
            <Text style={styles.reasonText}>{r}</Text>
          </View>
        ))}
      </View>

      {/* ---- Likely Species ---- */}
      {hotspot.species.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>🐟 Likely Shark Species</Text>
          {hotspot.species.map((sp) => {
            const info = SPECIES_FACTS[sp];
            return (
              <View key={sp} style={styles.speciesCard}>
                <Text style={styles.speciesEmoji}>{info?.emoji ?? "🦈"}</Text>
                <View style={styles.speciesInfo}>
                  <Text style={styles.speciesName}>{sp}</Text>
                  {info && (
                    <>
                      <Text style={styles.speciesDetail}>🍽️ Eats: {info.diet}</Text>
                      <Text style={styles.speciesDetail}>📏 Size: {info.size}</Text>
                      <View style={styles.factBubble}>
                        <Text style={styles.factText}>💡 {info.fact}</Text>
                      </View>
                    </>
                  )}
                </View>
              </View>
            );
          })}
        </>
      )}

      {/* ---- Safety Box ---- */}
      <View style={[styles.safetyBox, { borderColor: riskColor }]}>
        <Text style={[styles.safetyTitle, { color: riskColor }]}>
          {hotspot.risk_level === "high" ? "⚠️ Safety Notice" : hotspot.risk_level === "medium" ? "🔶 Be Aware" : "✅ Ocean Safety"}
        </Text>
        <Text style={styles.safetyText}>
          {hotspot.risk_level === "high"
            ? "Our model shows HIGH shark activity here. Avoid swimming or surfing in this area. Check with local beach authorities before entering the water."
            : hotspot.risk_level === "medium"
            ? "MODERATE shark activity predicted. Swim in groups, avoid dawn and dusk, and stay away from areas where people are fishing."
            : "LOW shark activity detected here. Standard ocean safety applies — always swim with a buddy and be aware of your surroundings."}
        </Text>
      </View>

      {/* ---- Data Source Note ---- */}
      <View style={styles.dataNote}>
        <Ionicons name="satellite-outline" size={14} color="#4A7FA5" />
        <Text style={styles.dataNoteText}>
          Powered by NASA PACE, GHRSST, and SWOT satellite data
        </Text>
      </View>
    </ScrollView>
  );
}

// ---- Sub-components ----
function OceanStat({ icon, label, value, note }: { icon: string; label: string; value: string; note: string }) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statIcon}>{icon}</Text>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statNote}>{note}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#050D1A" },

  heroCard: {
    margin: 16, borderRadius: 20, padding: 24,
    alignItems: "center", borderWidth: 1.5,
  },
  heroEmoji: { fontSize: 48, marginBottom: 8 },
  heroTitle: { color: "#CEE9F7", fontSize: 22, fontWeight: "800", marginBottom: 12 },
  riskPill: { borderRadius: 20, paddingHorizontal: 18, paddingVertical: 8, marginBottom: 10 },
  riskPillText: { color: "#fff", fontWeight: "700", fontSize: 15 },
  coordText: { color: "#4A7FA5", fontSize: 13 },

  sectionTitle: {
    color: "#CEE9F7", fontSize: 17, fontWeight: "700",
    marginLeft: 16, marginBottom: 10, marginTop: 6,
  },

  statsGrid: {
    flexDirection: "row", flexWrap: "wrap",
    paddingHorizontal: 12, gap: 8, marginBottom: 8,
  },
  statCard: {
    backgroundColor: "#071525", borderRadius: 14,
    padding: 14, width: "47%", borderWidth: 1, borderColor: "#0A2540",
  },
  statIcon: { fontSize: 22, marginBottom: 6 },
  statValue: { color: "#CEE9F7", fontSize: 18, fontWeight: "700" },
  statLabel: { color: "#4A7FA5", fontSize: 12, marginTop: 2 },
  statNote: { color: "#29678A", fontSize: 10, marginTop: 4 },

  reasonsCard: {
    marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 16, padding: 4, marginBottom: 8,
    borderWidth: 1, borderColor: "#0A2540",
  },
  reasonRow: { padding: 14 },
  reasonBorder: { borderBottomWidth: 1, borderBottomColor: "#0A2540" },
  reasonText: { color: "#B0D8ED", fontSize: 14, lineHeight: 22 },

  speciesCard: {
    flexDirection: "row",
    backgroundColor: "#071525",
    borderRadius: 16, marginHorizontal: 16, marginBottom: 10,
    padding: 14, borderWidth: 1, borderColor: "#0A2540",
  },
  speciesEmoji: { fontSize: 36, marginRight: 14 },
  speciesInfo: { flex: 1 },
  speciesName: { color: "#CEE9F7", fontSize: 16, fontWeight: "700", marginBottom: 4 },
  speciesDetail: { color: "#4A7FA5", fontSize: 13, marginBottom: 2 },
  factBubble: {
    backgroundColor: "#0A2540", borderRadius: 8,
    padding: 8, marginTop: 6,
  },
  factText: { color: "#8AB9CE", fontSize: 12 },

  safetyBox: {
    margin: 16, borderRadius: 16, padding: 16,
    borderWidth: 1.5, backgroundColor: "#071525",
  },
  safetyTitle: { fontSize: 16, fontWeight: "700", marginBottom: 8 },
  safetyText: { color: "#8AB9CE", fontSize: 14, lineHeight: 22 },

  dataNote: {
    flexDirection: "row", alignItems: "center", gap: 8,
    marginHorizontal: 16, marginTop: 4,
  },
  dataNoteText: { color: "#4A7FA5", fontSize: 11 },
});
