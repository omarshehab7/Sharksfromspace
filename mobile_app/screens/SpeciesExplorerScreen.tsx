/**
 * SpeciesExplorerScreen.tsx — Species Explorer
 *
 * Browse 7 shark species with habitat preferences,
 * temperature ranges, and predicted active regions.
 * Built for general users — no scientific jargon.
 */

import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const { width } = Dimensions.get("window");

// ---- Species Data ----
const SPECIES = [
  {
    id: "great_white",
    name: "Great White Shark",
    emoji: "🦈",
    nickname: "The Ocean Apex",
    color: "#EF4444",
    gradient: "#7F1D1D",
    temperature: { min: 12, max: 24, ideal: 18 },
    depth: "0–1,200m",
    regions: ["North Pacific", "North Atlantic", "South Africa", "Australia"],
    status: "Vulnerable",
    statusColor: "#F59E0B",
    size: "Up to 6m • 2,000 kg",
    diet: "Seals, sea lions, large fish, dolphins",
    speed: "Up to 56 km/h",
    lifespan: "70+ years",
    blurb:
      "The iconic Great White prefers cool, productive coastal waters. They're highly migratory and follow warm-blooded prey like seals across entire ocean basins.",
    funFacts: [
      "They can detect one drop of blood in 100 liters of water",
      "Great whites are warm-blooded — unusual for fish",
      "They can breach completely out of the water at speed",
    ],
    habitatNote: "Look for them near continental shelves where cool, nutrient-rich water meets warmer surface water.",
  },
  {
    id: "tiger",
    name: "Tiger Shark",
    emoji: "🦈",
    nickname: "The Opportunist",
    color: "#F59E0B",
    gradient: "#78350F",
    temperature: { min: 20, max: 30, ideal: 26 },
    depth: "0–350m",
    regions: ["Caribbean", "Gulf of Mexico", "Indo-Pacific", "Hawaii"],
    status: "Near Threatened",
    statusColor: "#F59E0B",
    size: "Up to 5.5m • 900 kg",
    diet: "Sea turtles, rays, smaller sharks, almost anything",
    speed: "Up to 32 km/h",
    lifespan: "27+ years",
    blurb:
      "Tiger sharks love warm, murky coastal waters and are famously non-picky eaters. Their distinctive stripes fade as they grow older.",
    funFacts: [
      "Found license plates and rubber tires in their stomachs",
      "Second most dangerous shark to humans after the Great White",
      "Can detect electric fields from other animals",
    ],
    habitatNote: "Thrive in warm tropical and subtropical waters, often near coral reefs and river mouths.",
  },
  {
    id: "hammerhead",
    name: "Hammerhead Shark",
    emoji: "🦈",
    nickname: "The 360° Hunter",
    color: "#8B5CF6",
    gradient: "#4C1D95",
    temperature: { min: 18, max: 28, ideal: 23 },
    depth: "0–300m",
    regions: ["Tropical worldwide", "Caribbean", "Galapagos", "Bahamas"],
    status: "Critically Endangered",
    statusColor: "#EF4444",
    size: "Up to 4m • 580 kg",
    diet: "Stingrays, squid, octopus, fish",
    speed: "Up to 40 km/h",
    lifespan: "20–30 years",
    blurb:
      "The extraordinary hammer-shaped head (called a cephalofoil) gives hammerheads near-360° vision and superior electroreception to find buried prey.",
    funFacts: [
      "Their wide head acts like a wing for better swimming maneuverability",
      "They are immune to stingray venom",
      "Often found in schooling groups of hundreds",
    ],
    habitatNote: "Concentrate around seamounts and islands where currents push prey upward.",
  },
  {
    id: "blue",
    name: "Blue Shark",
    emoji: "🦈",
    nickname: "The Global Wanderer",
    color: "#3B82F6",
    gradient: "#1E3A8A",
    temperature: { min: 10, max: 22, ideal: 16 },
    depth: "0–600m",
    regions: ["Open ocean worldwide", "North Atlantic", "Mediterranean"],
    status: "Near Threatened",
    statusColor: "#F59E0B",
    size: "Up to 3.8m • 200 kg",
    diet: "Squid, small fish, krill",
    speed: "Up to 40 km/h",
    lifespan: "20+ years",
    blurb:
      "Blue sharks are the most wide-ranging shark species on Earth, crossing entire ocean basins in circular migration patterns following the currents.",
    funFacts: [
      "Can travel 9,000 km in a single year",
      "Their deep blue color provides camouflage in open water",
      "Most heavily fished shark species — 10–20 million caught per year",
    ],
    habitatNote: "Found in the open ocean (pelagic zone), preferring cool, offshore water far from coastlines.",
  },
  {
    id: "whale",
    name: "Whale Shark",
    emoji: "🐋",
    nickname: "The Gentle Giant",
    color: "#22C55E",
    gradient: "#14532D",
    temperature: { min: 21, max: 30, ideal: 26 },
    depth: "0–1,900m",
    regions: ["Tropical worldwide", "Coral Triangle", "Mexico (Yucatan)", "Maldives"],
    status: "Endangered",
    statusColor: "#EF4444",
    size: "Up to 12m • 20,000 kg",
    diet: "Plankton, krill, small fish, fish eggs",
    speed: "Up to 5 km/h",
    lifespan: "70–150 years",
    blurb:
      "The largest fish in the ocean — and completely harmless to humans! Whale sharks are filter feeders, swimming slowly with their mouths open to sieve plankton.",
    funFacts: [
      "Their mouth can be 1.5m wide",
      "Each whale shark has a unique spot pattern like a fingerprint",
      "Filters over 6,000 liters of water per hour",
    ],
    habitatNote: "Follow plankton blooms. Appear in huge numbers at coral spawning events where food is abundant.",
  },
  {
    id: "bull",
    name: "Bull Shark",
    emoji: "🦈",
    nickname: "The River Shark",
    color: "#64748B",
    gradient: "#1E293B",
    temperature: { min: 20, max: 32, ideal: 27 },
    depth: "0–150m",
    regions: ["Tropical coastlines", "Florida", "Caribbean", "South Africa", "Ganges River"],
    status: "Vulnerable",
    statusColor: "#F59E0B",
    size: "Up to 3.4m • 315 kg",
    diet: "Fish, dolphins, other sharks, birds",
    speed: "Up to 40 km/h",
    lifespan: "16+ years",
    blurb:
      "Bull sharks can survive in both salt and fresh water, making them unique. They've been found hundreds of miles up rivers, including the Amazon and Mississippi.",
    funFacts: [
      "Can regulate their kidneys to survive in freshwater",
      "Most aggressive shark species — territorial and unpredictable",
      "Responsible for many inland river 'shark attacks'",
    ],
    habitatNote: "Coastal and riverine — found in shallow, warm, murky water near populated areas.",
  },
  {
    id: "mako",
    name: "Mako Shark",
    emoji: "🦈",
    nickname: "The Speed Demon",
    color: "#06B6D4",
    gradient: "#164E63",
    temperature: { min: 15, max: 25, ideal: 20 },
    depth: "0–500m",
    regions: ["Open ocean worldwide", "Mediterranean", "North Atlantic"],
    status: "Endangered",
    statusColor: "#EF4444",
    size: "Up to 4m • 570 kg",
    diet: "Tuna, swordfish, billfish, squid",
    speed: "Up to 80 km/h",
    lifespan: "28–35 years",
    blurb:
      "The Mako is the world's fastest shark, capable of bursting to 80 km/h to catch fast-swimming tuna and swordfish. It can leap up to 9 meters out of the water.",
    funFacts: [
      "Fastest shark on Earth — faster than a cheetah in the water",
      "Can maintain body temperature above water temperature",
      "Has been found to be nearly as intelligent as a dog",
    ],
    habitatNote: "Prefers open water temperature boundaries (fronts) where warm and cool water meet — same areas where tuna congregate.",
  },
];

// ---- Component ----
export default function SpeciesExplorerScreen() {
  const insets = useSafeAreaInsets();
  const [selected, setSelected] = useState<typeof SPECIES[0] | null>(null);

  if (selected) {
    return <SpeciesDetail species={selected} onBack={() => setSelected(null)} />;
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>🦈 Species Explorer</Text>
        <Text style={styles.headerSub}>Tap a shark to learn more</Text>
      </View>
      <ScrollView contentContainerStyle={styles.gridContainer} showsVerticalScrollIndicator={false}>
        {SPECIES.map((sp) => (
          <TouchableOpacity
            key={sp.id}
            style={[styles.card, { borderColor: sp.color + "44", backgroundColor: sp.gradient + "33" }]}
            onPress={() => setSelected(sp)}
            activeOpacity={0.8}
          >
            <View style={[styles.cardEmoji, { backgroundColor: sp.color + "22" }]}>
              <Text style={{ fontSize: 36 }}>{sp.emoji}</Text>
            </View>
            <Text style={[styles.cardName, { color: sp.color }]}>{sp.name}</Text>
            <Text style={styles.cardNickname}>{sp.nickname}</Text>
            <View style={styles.tempRow}>
              <Ionicons name="thermometer-outline" size={12} color="#4A7FA5" />
              <Text style={styles.tempText}>{sp.temperature.min}–{sp.temperature.max}°C</Text>
            </View>
            <View style={[styles.statusPill, { backgroundColor: sp.statusColor + "22", borderColor: sp.statusColor + "55" }]}>
              <Text style={[styles.statusText, { color: sp.statusColor }]}>{sp.status}</Text>
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

// ---- Detail View ----
function SpeciesDetail({ species: sp, onBack }: { species: typeof SPECIES[0]; onBack: () => void }) {
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Top bar */}
      <View style={styles.detailHeader}>
        <TouchableOpacity onPress={onBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={22} color="#CEE9F7" />
        </TouchableOpacity>
        <Text style={styles.detailHeaderTitle}>Species Profile</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 50 }}>
        {/* Hero */}
        <View style={[styles.detailHero, { backgroundColor: sp.gradient + "55", borderColor: sp.color + "44" }]}>
          <Text style={{ fontSize: 72 }}>{sp.emoji}</Text>
          <Text style={[styles.detailName, { color: sp.color }]}>{sp.name}</Text>
          <Text style={styles.detailNickname}>{sp.nickname}</Text>
          <View style={[styles.statusPill, { backgroundColor: sp.statusColor + "22", borderColor: sp.statusColor + "55", marginTop: 8 }]}>
            <Text style={[styles.statusText, { color: sp.statusColor }]}>Conservation: {sp.status}</Text>
          </View>
        </View>

        {/* Quick Stats */}
        <View style={styles.quickStats}>
          <QuickStat icon="📏" label="Size" value={sp.size} />
          <QuickStat icon="⚡" label="Top Speed" value={sp.speed} />
          <QuickStat icon="⏳" label="Lifespan" value={sp.lifespan} />
          <QuickStat icon="🌊" label="Depth Range" value={sp.depth} />
        </View>

        {/* Temperature Preference */}
        <Text style={styles.sectionTitle}>🌡️ Preferred Temperature</Text>
        <View style={styles.tempCard}>
          <View style={styles.tempBar}>
            <View style={styles.tempScale}>
              <View style={[styles.tempFill, {
                left: `${((sp.temperature.min + 5) / 45) * 100}%` as any,
                width: `${((sp.temperature.max - sp.temperature.min) / 45) * 100}%` as any,
                backgroundColor: sp.color,
              }]} />
              <View style={[styles.tempIdeal, {
                left: `${((sp.temperature.ideal + 5) / 45) * 100}%` as any,
                backgroundColor: "#fff",
              }]} />
            </View>
            <View style={styles.tempLabels}>
              <Text style={styles.tempLabelText}>0°C</Text>
              <Text style={styles.tempLabelText}>45°C</Text>
            </View>
          </View>
          <Text style={styles.tempRange}>
            Prefers {sp.temperature.min}°C – {sp.temperature.max}°C · Sweet spot: {sp.temperature.ideal}°C
          </Text>
        </View>

        {/* Habitat */}
        <Text style={styles.sectionTitle}>📍 Where to Find Them</Text>
        <View style={styles.infoCard}>
          <Text style={styles.infoText}>{sp.habitatNote}</Text>
          <View style={styles.regionWrap}>
            {sp.regions.map((r) => (
              <View key={r} style={[styles.regionChip, { borderColor: sp.color + "44" }]}>
                <Text style={[styles.regionText, { color: sp.color }]}>{r}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Diet */}
        <Text style={styles.sectionTitle}>🍽️ What They Eat</Text>
        <View style={styles.infoCard}>
          <Text style={styles.infoText}>{sp.diet}</Text>
        </View>

        {/* About */}
        <Text style={styles.sectionTitle}>📖 About</Text>
        <View style={styles.infoCard}>
          <Text style={styles.infoText}>{sp.blurb}</Text>
        </View>

        {/* Fun Facts */}
        <Text style={styles.sectionTitle}>🤩 Cool Facts</Text>
        {sp.funFacts.map((fact, i) => (
          <View key={i} style={styles.factRow}>
            <View style={[styles.factNumber, { backgroundColor: sp.color }]}>
              <Text style={{ color: "#050D1A", fontWeight: "800", fontSize: 12 }}>{i + 1}</Text>
            </View>
            <Text style={styles.factText}>{fact}</Text>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

function QuickStat({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <View style={styles.quickStatItem}>
      <Text style={{ fontSize: 20 }}>{icon}</Text>
      <Text style={styles.quickStatValue}>{value}</Text>
      <Text style={styles.quickStatLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#050D1A" },

  header: { paddingHorizontal: 16, paddingVertical: 14 },
  headerTitle: { color: "#CEE9F7", fontSize: 26, fontWeight: "800" },
  headerSub: { color: "#4A7FA5", fontSize: 14, marginTop: 2 },

  gridContainer: {
    flexDirection: "row", flexWrap: "wrap",
    padding: 12, gap: 10,
  },
  card: {
    width: (width - 34) / 2,
    borderRadius: 18, padding: 16,
    alignItems: "center", borderWidth: 1,
  },
  cardEmoji: { width: 64, height: 64, borderRadius: 32, alignItems: "center", justifyContent: "center", marginBottom: 10 },
  cardName: { fontSize: 14, fontWeight: "700", textAlign: "center", marginBottom: 4 },
  cardNickname: { color: "#4A7FA5", fontSize: 11, textAlign: "center", marginBottom: 8 },
  tempRow: { flexDirection: "row", alignItems: "center", gap: 4, marginBottom: 8 },
  tempText: { color: "#4A7FA5", fontSize: 11 },
  statusPill: { borderRadius: 12, paddingHorizontal: 10, paddingVertical: 4, borderWidth: 1 },
  statusText: { fontSize: 11, fontWeight: "600" },

  detailHeader: {
    flexDirection: "row", alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16, paddingBottom: 10,
  },
  backBtn: { width: 40, height: 40, alignItems: "center", justifyContent: "center" },
  detailHeaderTitle: { color: "#CEE9F7", fontSize: 17, fontWeight: "700" },

  detailHero: {
    margin: 16, borderRadius: 20, padding: 24,
    alignItems: "center", borderWidth: 1,
  },
  detailName: { fontSize: 24, fontWeight: "800", marginTop: 10, textAlign: "center" },
  detailNickname: { color: "#4A7FA5", fontSize: 14, marginTop: 4 },

  quickStats: {
    flexDirection: "row",
    marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 16, paddingVertical: 16, marginBottom: 8,
    borderWidth: 1, borderColor: "#0A2540",
  },
  quickStatItem: { flex: 1, alignItems: "center" },
  quickStatValue: { color: "#CEE9F7", fontSize: 13, fontWeight: "700", marginTop: 4, textAlign: "center" },
  quickStatLabel: { color: "#4A7FA5", fontSize: 10, marginTop: 2 },

  sectionTitle: {
    color: "#CEE9F7", fontSize: 16, fontWeight: "700",
    marginLeft: 16, marginTop: 14, marginBottom: 8,
  },

  tempCard: {
    marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 14, padding: 16, borderWidth: 1, borderColor: "#0A2540", marginBottom: 4,
  },
  tempBar: { marginBottom: 10 },
  tempScale: {
    height: 10, backgroundColor: "#0A2540", borderRadius: 5,
    position: "relative", marginBottom: 6,
  },
  tempFill: { position: "absolute", height: "100%", borderRadius: 5, opacity: 0.8 },
  tempIdeal: { position: "absolute", width: 4, height: "100%", borderRadius: 2 },
  tempLabels: { flexDirection: "row", justifyContent: "space-between" },
  tempLabelText: { color: "#4A7FA5", fontSize: 10 },
  tempRange: { color: "#8AB9CE", fontSize: 13 },

  infoCard: {
    marginHorizontal: 16, backgroundColor: "#071525",
    borderRadius: 14, padding: 14, borderWidth: 1, borderColor: "#0A2540", marginBottom: 4,
  },
  infoText: { color: "#B0D8ED", fontSize: 14, lineHeight: 22 },

  regionWrap: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 10 },
  regionChip: {
    borderRadius: 14, paddingHorizontal: 10, paddingVertical: 4,
    borderWidth: 1, backgroundColor: "#0A2540",
  },
  regionText: { fontSize: 12 },

  factRow: {
    flexDirection: "row", alignItems: "flex-start",
    marginHorizontal: 16, marginBottom: 10, gap: 12,
  },
  factNumber: { width: 24, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center", marginTop: 1 },
  factText: { color: "#B0D8ED", fontSize: 14, lineHeight: 22, flex: 1 },
});
