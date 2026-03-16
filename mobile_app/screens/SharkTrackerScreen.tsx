/**
 * SharkTrackerScreen.tsx — Simulated Shark Tag Data
 *
 * Displays animated simulated satellite tag data:
 * - Named shark individuals with location + movement
 * - Dive depth profile
 * - Feeding probability
 * - Movement pattern visualization
 */

import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Easing,
  Dimensions,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const { width } = Dimensions.get("window");

// ---- Simulated Tag Data ----
const TAGGED_SHARKS = [
  {
    id: "t1",
    name: "Nova",
    species: "Great White Shark",
    tagId: "GW-2847",
    emoji: "🦈",
    color: "#EF4444",
    sex: "Female",
    size: 4.8,
    weightKg: 820,
    tagDate: "Oct 2024",
    latitude: 28.4,
    longitude: -79.1,
    divesPerDay: 18,
    maxDepthM: 612,
    currentDepthM: 47,
    feedingProbability: 0.78,
    movementPattern: "Coastal patrol — following prey school northward",
    status: "Active",
    distanceTodayKm: 63,
    diveProfile: [0, 45, 82, 140, 210, 320, 450, 612, 380, 190, 80, 20, 5, 15, 90, 180, 420, 510, 200, 30],
  },
  {
    id: "t2",
    name: "Titan",
    species: "Tiger Shark",
    tagId: "TS-1192",
    emoji: "🦈",
    color: "#F59E0B",
    sex: "Male",
    size: 3.9,
    weightKg: 410,
    tagDate: "Feb 2025",
    latitude: 24.7,
    longitude: -76.3,
    divesPerDay: 12,
    maxDepthM: 290,
    currentDepthM: 8,
    feedingProbability: 0.34,
    movementPattern: "Reef patrol — circling reef system",
    status: "Shallow",
    distanceTodayKm: 31,
    diveProfile: [0, 8, 15, 30, 45, 80, 130, 200, 250, 290, 220, 160, 90, 40, 15, 5, 2, 10, 25, 8],
  },
  {
    id: "t3",
    name: "Luna",
    species: "Hammerhead Shark",
    tagId: "HH-0559",
    emoji: "🦈",
    color: "#8B5CF6",
    sex: "Female",
    size: 3.4,
    weightKg: 290,
    tagDate: "Jan 2025",
    latitude: 32.1,
    longitude: -77.8,
    divesPerDay: 22,
    maxDepthM: 185,
    currentDepthM: 62,
    feedingProbability: 0.91,
    movementPattern: "Deep dive sequence — active hunting mode",
    status: "Hunting",
    distanceTodayKm: 88,
    diveProfile: [0, 20, 55, 90, 130, 165, 185, 170, 145, 100, 60, 30, 8, 25, 70, 120, 175, 185, 160, 90],
  },
  {
    id: "t4",
    name: "Atlas",
    species: "Blue Shark",
    tagId: "BS-3371",
    emoji: "🦈",
    color: "#3B82F6",
    sex: "Male",
    size: 2.8,
    weightKg: 90,
    tagDate: "Dec 2024",
    latitude: 36.5,
    longitude: -69.2,
    divesPerDay: 30,
    maxDepthM: 420,
    currentDepthM: 310,
    feedingProbability: 0.22,
    movementPattern: "Open ocean transit — migrating north",
    status: "Migrating",
    distanceTodayKm: 142,
    diveProfile: [0, 50, 120, 200, 300, 380, 420, 390, 330, 260, 180, 100, 50, 10, 80, 200, 350, 420, 300, 150],
  },
];

const STATUS_COLOR: Record<string, string> = {
  Active: "#22C55E",
  Shallow: "#3B82F6",
  Hunting: "#EF4444",
  Migrating: "#8B5CF6",
  Resting: "#6B7280",
};

// ---- Main Component ----
export default function SharkTrackerScreen() {
  const insets = useSafeAreaInsets();
  const [selected, setSelected] = useState<typeof TAGGED_SHARKS[0]>(TAGGED_SHARKS[0]);
  const pulseAnim = useRef(new Animated.Value(0.8)).current;
  const depthAnim = useRef(new Animated.Value(0)).current;

  // Pulse animation for active shark
  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.15, duration: 900, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 0.8, duration: 900, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, []);

  // Animate depth bar on selection change
  useEffect(() => {
    depthAnim.setValue(0);
    Animated.timing(depthAnim, { toValue: 1, duration: 800, easing: Easing.out(Easing.exp), useNativeDriver: false }).start();
  }, [selected.id]);

  const depthPct = selected.currentDepthM / selected.maxDepthM;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>📡 Shark Tracker</Text>
        <Text style={styles.headerSub}>Live simulated tag data</Text>
      </View>

      {/* Shark Selector */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.selectorRow}
      >
        {TAGGED_SHARKS.map((sh) => (
          <TouchableOpacity
            key={sh.id}
            style={[
              styles.selectorCard,
              selected.id === sh.id && { borderColor: sh.color, backgroundColor: sh.color + "18" },
            ]}
            onPress={() => setSelected(sh)}
            activeOpacity={0.8}
          >
            <Text style={{ fontSize: 24 }}>{sh.emoji}</Text>
            <Text style={[styles.selectorName, selected.id === sh.id && { color: sh.color }]}>{sh.name}</Text>
            <Text style={styles.selectorSpecies}>{sh.species.split(" ")[0]}</Text>
            <View style={[styles.statusDot, { backgroundColor: STATUS_COLOR[sh.status] }]} />
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Main Content */}
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 50 }}>
        {/* Identity Card */}
        <View style={[styles.identityCard, { borderColor: selected.color + "44" }]}>
          <View style={styles.identityTop}>
            <View>
              <Text style={[styles.sharkName, { color: selected.color }]}>{selected.name}</Text>
              <Text style={styles.sharkSpecies}>{selected.species}</Text>
              <Text style={styles.tagId}>Tag ID: {selected.tagId} · Tagged {selected.tagDate}</Text>
            </View>
            <Animated.View style={[styles.pulseDot, { backgroundColor: selected.color, transform: [{ scale: pulseAnim }] }]}>
              <View style={[styles.pulseDotInner, { backgroundColor: selected.color }]} />
            </Animated.View>
          </View>
          <View style={styles.bioRow}>
            <BioChip label="Sex" value={selected.sex} />
            <BioChip label="Length" value={`${selected.size}m`} />
            <BioChip label="Weight" value={`${selected.weightKg} kg`} />
          </View>
        </View>

        {/* Current Status */}
        <Text style={styles.sectionTitle}>📍 Right Now</Text>
        <View style={styles.statusCard}>
          <View style={[styles.statusBanner, { backgroundColor: STATUS_COLOR[selected.status] + "22", borderColor: STATUS_COLOR[selected.status] }]}>
            <View style={[styles.statusBannerDot, { backgroundColor: STATUS_COLOR[selected.status] }]} />
            <Text style={[styles.statusBannerText, { color: STATUS_COLOR[selected.status] }]}>{selected.status}</Text>
          </View>
          <Text style={styles.movementText}>{selected.movementPattern}</Text>
          <View style={styles.coordRow}>
            <Ionicons name="location-outline" size={14} color="#4A7FA5" />
            <Text style={styles.coordText}>
              {Math.abs(selected.latitude).toFixed(2)}°{selected.latitude >= 0 ? "N" : "S"},{"  "}
              {Math.abs(selected.longitude).toFixed(2)}°{selected.longitude <= 0 ? "W" : "E"}
            </Text>
          </View>
        </View>

        {/* Stats Grid */}
        <View style={styles.statsGrid}>
          <StatItem icon="📏" label="Distance Today" value={`${selected.distanceTodayKm} km`} />
          <StatItem icon="🤿" label="Dives Today" value={`${selected.divesPerDay}`} />
          <StatItem icon="⬇️" label="Max Depth" value={`${selected.maxDepthM} m`} />
          <StatItem icon="📍" label="Now at" value={`${selected.currentDepthM} m deep`} />
        </View>

        {/* Depth Gauge */}
        <Text style={styles.sectionTitle}>🌊 Dive Depth</Text>
        <View style={styles.depthCard}>
          <View style={styles.depthGauge}>
            <View style={styles.depthTrack}>
              <Animated.View
                style={[
                  styles.depthFill,
                  {
                    height: depthAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: ["0%", `${depthPct * 100}%`],
                    }),
                    backgroundColor: selected.color,
                  },
                ]}
              />
            </View>
            <View style={styles.depthLabels}>
              <Text style={styles.depthLabel}>Surface</Text>
              <Text style={[styles.depthValue, { color: selected.color }]}>{selected.currentDepthM}m</Text>
              <Text style={styles.depthLabel}>{selected.maxDepthM}m</Text>
            </View>
          </View>
          <Text style={styles.depthHint}>
            {selected.currentDepthM < 30
              ? "🌅 Near the surface — likely resting or hunting surface prey"
              : selected.currentDepthM < 150
              ? "🐠 Mid-water hunting — chasing fish and schooling prey"
              : "🦑 Deep dive — hunting squid or following temperature layers"}
          </Text>
        </View>

        {/* Dive Profile Chart */}
        <Text style={styles.sectionTitle}>📊 24-Hour Dive Profile</Text>
        <View style={styles.chartCard}>
          <View style={styles.chart}>
            {selected.diveProfile.map((depth, i) => {
              const barH = (depth / selected.maxDepthM) * 80;
              return (
                <View key={i} style={styles.chartBarWrap}>
                  <View style={{ height: 80, justifyContent: "flex-end" }}>
                    <View style={[styles.chartBar, { height: barH, backgroundColor: selected.color }]} />
                  </View>
                </View>
              );
            })}
          </View>
          <View style={styles.chartXAxis}>
            <Text style={styles.chartLabel}>Midnight</Text>
            <Text style={styles.chartLabel}>6am</Text>
            <Text style={styles.chartLabel}>Noon</Text>
            <Text style={styles.chartLabel}>6pm</Text>
            <Text style={styles.chartLabel}>Now</Text>
          </View>
          <Text style={styles.chartNote}>↓ Downward = deeper dive. Peak depth: {selected.maxDepthM}m</Text>
        </View>

        {/* Feeding Probability */}
        <Text style={styles.sectionTitle}>🍽️ Feeding Likelihood</Text>
        <View style={styles.feedingCard}>
          <View style={styles.feedingRow}>
            <Text style={styles.feedingPct}>{Math.round(selected.feedingProbability * 100)}%</Text>
            <View style={styles.feedingBar}>
              <Animated.View
                style={[
                  styles.feedingFill,
                  {
                    width: `${selected.feedingProbability * 100}%` as any,
                    backgroundColor: selected.feedingProbability > 0.6 ? "#EF4444"
                      : selected.feedingProbability > 0.3 ? "#F59E0B" : "#22C55E",
                  },
                ]}
              />
            </View>
          </View>
          <Text style={styles.feedingDesc}>
            {selected.feedingProbability > 0.7
              ? "🔴 Very likely feeding right now based on dive pattern and location"
              : selected.feedingProbability > 0.4
              ? "🟡 Possibly searching for food — dive pattern shows hunting behavior"
              : "🟢 Probably not actively feeding — movement suggests transit or resting"}
          </Text>
        </View>

        {/* Tag Info */}
        <View style={styles.tagNote}>
          <Ionicons name="information-circle-outline" size={14} color="#4A7FA5" />
          <Text style={styles.tagNoteText}>
            This is simulated data based on real behavioral studies. Actual satellite tagging programs transmit via ARGOS satellites when the shark surfaces.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

function BioChip({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.bioChip}>
      <Text style={styles.bioLabel}>{label}</Text>
      <Text style={styles.bioValue}>{value}</Text>
    </View>
  );
}

function StatItem({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <View style={styles.statItem}>
      <Text style={{ fontSize: 18 }}>{icon}</Text>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#050D1A" },

  header: { paddingHorizontal: 16, paddingVertical: 14 },
  headerTitle: { color: "#CEE9F7", fontSize: 26, fontWeight: "800" },
  headerSub: { color: "#4A7FA5", fontSize: 14, marginTop: 2 },

  selectorRow: { paddingHorizontal: 12, paddingBottom: 12, gap: 8 },
  selectorCard: {
    width: 86, borderRadius: 14, padding: 12,
    alignItems: "center", borderWidth: 1.5,
    borderColor: "#0A2540", backgroundColor: "#071525",
  },
  selectorName: { color: "#CEE9F7", fontWeight: "700", fontSize: 14, marginTop: 4 },
  selectorSpecies: { color: "#4A7FA5", fontSize: 10, marginTop: 2, textAlign: "center" },
  statusDot: { width: 8, height: 8, borderRadius: 4, marginTop: 6 },

  identityCard: {
    marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 18, padding: 18, borderWidth: 1, marginBottom: 8,
  },
  identityTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 },
  sharkName: { fontSize: 24, fontWeight: "800" },
  sharkSpecies: { color: "#8AB9CE", fontSize: 14, marginTop: 2 },
  tagId: { color: "#4A7FA5", fontSize: 12, marginTop: 4 },
  pulseDot: {
    width: 36, height: 36, borderRadius: 18,
    alignItems: "center", justifyContent: "center", opacity: 0.4,
  },
  pulseDotInner: { width: 16, height: 16, borderRadius: 8 },

  bioRow: { flexDirection: "row", gap: 8 },
  bioChip: {
    backgroundColor: "#0A2540", borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 8, flex: 1, alignItems: "center",
  },
  bioLabel: { color: "#4A7FA5", fontSize: 10 },
  bioValue: { color: "#CEE9F7", fontWeight: "700", fontSize: 14, marginTop: 2 },

  sectionTitle: {
    color: "#CEE9F7", fontSize: 16, fontWeight: "700",
    marginLeft: 16, marginTop: 12, marginBottom: 8,
  },

  statusCard: {
    marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 14, padding: 14, borderWidth: 1, borderColor: "#0A2540", marginBottom: 4,
  },
  statusBanner: {
    flexDirection: "row", alignItems: "center", gap: 8,
    borderRadius: 10, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 8, marginBottom: 10,
  },
  statusBannerDot: { width: 8, height: 8, borderRadius: 4 },
  statusBannerText: { fontWeight: "700", fontSize: 14 },
  movementText: { color: "#B0D8ED", fontSize: 14, lineHeight: 20, marginBottom: 8 },
  coordRow: { flexDirection: "row", alignItems: "center", gap: 4 },
  coordText: { color: "#4A7FA5", fontSize: 12 },

  statsGrid: {
    flexDirection: "row", marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 14, paddingVertical: 14, borderWidth: 1, borderColor: "#0A2540", marginBottom: 4,
  },
  statItem: { flex: 1, alignItems: "center" },
  statValue: { color: "#CEE9F7", fontWeight: "700", fontSize: 13, marginTop: 4, textAlign: "center" },
  statLabel: { color: "#4A7FA5", fontSize: 10, marginTop: 2, textAlign: "center" },

  depthCard: {
    marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 14, padding: 16, borderWidth: 1, borderColor: "#0A2540", marginBottom: 4,
  },
  depthGauge: { flexDirection: "row", alignItems: "stretch", height: 100, gap: 14 },
  depthTrack: {
    width: 20, backgroundColor: "#0A2540", borderRadius: 10,
    overflow: "hidden", justifyContent: "flex-end",
  },
  depthFill: { borderRadius: 10 },
  depthLabels: { flex: 1, justifyContent: "space-between", paddingVertical: 2 },
  depthLabel: { color: "#4A7FA5", fontSize: 11 },
  depthValue: { fontSize: 20, fontWeight: "800" },
  depthHint: { color: "#8AB9CE", fontSize: 13, marginTop: 14, lineHeight: 20 },

  chartCard: {
    marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 14, padding: 16, borderWidth: 1, borderColor: "#0A2540", marginBottom: 4,
  },
  chart: { flexDirection: "row", alignItems: "flex-end", height: 90, gap: 2 },
  chartBarWrap: { flex: 1 },
  chartBar: { borderRadius: 2, opacity: 0.85, width: "100%" },
  chartXAxis: { flexDirection: "row", justifyContent: "space-between", marginTop: 6 },
  chartLabel: { color: "#4A7FA5", fontSize: 9 },
  chartNote: { color: "#29678A", fontSize: 11, marginTop: 6 },

  feedingCard: {
    marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 14, padding: 16, borderWidth: 1, borderColor: "#0A2540", marginBottom: 4,
  },
  feedingRow: { flexDirection: "row", alignItems: "center", gap: 12, marginBottom: 12 },
  feedingPct: { color: "#CEE9F7", fontSize: 28, fontWeight: "800", width: 56 },
  feedingBar: {
    flex: 1, height: 10, backgroundColor: "#0A2540", borderRadius: 5, overflow: "hidden",
  },
  feedingFill: { height: "100%", borderRadius: 5 },
  feedingDesc: { color: "#8AB9CE", fontSize: 14, lineHeight: 20 },

  tagNote: {
    flexDirection: "row", alignItems: "flex-start", gap: 8,
    marginHorizontal: 16, marginTop: 8,
  },
  tagNoteText: { color: "#4A7FA5", fontSize: 11, flex: 1, lineHeight: 17 },
});
