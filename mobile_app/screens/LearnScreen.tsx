/**
 * LearnScreen.tsx — Educational Content
 *
 * Expandable accordion of science explainers in simple language.
 * No jargon — designed for curious non-scientists.
 */

import React, { useState, useRef } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Animated,
  StyleSheet,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const LEARN_SECTIONS = [
  {
    emoji: "🛰️",
    title: "How It Works",
    color: "#29ABE2",
    description:
      "We use NASA satellites orbiting hundreds of miles above Earth to measure ocean conditions — water temperature, plankton levels, and ocean circulation. Our AI model analyzes these patterns to predict where sharks are most likely to be active.",
    keyPoints: [
      "NASA PACE satellite measures plankton from space",
      "GHRSST measures ocean temperature at 1km resolution",
      "SWOT measures ocean circulation patterns",
      "AI model combines all data into a hotspot prediction",
    ],
  },
  {
    emoji: "🌡️",
    title: "Sea Temperature",
    color: "#F87171",
    description:
      "Satellites measure the ocean's surface temperature using infrared sensors — the same technology as thermal cameras. Sharks have temperature preferences, and they follow warm-water prey fish across ocean basins.",
    keyPoints: [
      "Most sharks prefer water between 18–28°C",
      "They hunt along 'thermal fronts' — the edge between warm and cold water",
      "Warm anomalies can signal unusual feeding opportunities",
      "Great whites love cool, nutrient-rich upwelling zones",
    ],
  },
  {
    emoji: "🟢",
    title: "Plankton & Ocean Food",
    color: "#4ADE80",
    description:
      "Chlorophyll is what makes plants green — in the ocean, it comes from tiny floating organisms called phytoplankton. More phytoplankton means more small fish, which means more sharks. It's the ocean's food chain, visible from space!",
    keyPoints: [
      "Phytoplankton are microscopic plants that form the base of all ocean food chains",
      "PACE satellite can detect different types of phytoplankton",
      "Bright green patches in the ocean = productive feeding zones",
      "Whale sharks follow plankton blooms across entire oceans",
    ],
  },
  {
    emoji: "🌀",
    title: "Ocean Eddies",
    color: "#818CF8",
    description:
      "Ocean eddies are massive spinning circles of water — some as large as 500km across. They work like giant 'mixers' that concentrate nutrients and trap prey fish in their core, creating natural feeding hotspots for sharks.",
    keyPoints: [
      "SWOT satellite maps sea surface height to detect eddies",
      "Cold-core eddies spin counterclockwise and upwell nutrients",
      "Warm-core eddies concentrate prey in their clockwise swirl",
      "Shark hotspots often align with eddy edges",
    ],
  },
  {
    emoji: "〰️",
    title: "Ocean Fronts",
    color: "#F59E0B",
    description:
      "Ocean fronts are like underwater walls where two different masses of water meet. Fish gather here because nutrients mix at the boundary. Think of it as a buffet line in the middle of the ocean — sharks know where to find it.",
    keyPoints: [
      "Fronts are detected by sharp temperature changes over short distances",
      "Prey fish school along frontal boundaries",
      "Mako sharks are famous for patrolling thermal fronts hunting tuna",
      "Some fronts are permanent features; others shift with seasons",
    ],
  },
  {
    emoji: "🤖",
    title: "The AI Model",
    color: "#EC4899",
    description:
      "Our prediction model combines all the satellite data into a single 'shark likelihood' score for each patch of ocean. It uses the same type of AI behind weather forecasting — trained on years of ocean data.",
    keyPoints: [
      "Weighted formula: SST + plankton + fronts + eddies",
      "Each factor is scored 0–100% based on shark preference",
      "Color-coded output: green (low) → yellow (medium) → red (high)",
      "Updates every 6 hours as new satellite passes occur",
    ],
  },
  {
    emoji: "🌍",
    title: "Conservation",
    color: "#34D399",
    description:
      "Sharks are critically important to ocean health — they keep fish populations balanced and healthy. By knowing where sharks are, we can protect them from fishing nets, and help beachgoers stay safe.",
    keyPoints: [
      "100 million sharks are killed by humans each year",
      "Many species take 15+ years to reach reproductive age",
      "Removing apex predators collapses entire reef ecosystems",
      "This app supports non-invasive shark tracking science",
    ],
  },
];

export default function LearnScreen() {
  const insets = useSafeAreaInsets();
  const [openIdx, setOpenIdx] = useState<number | null>(0);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>📚 Learn</Text>
        <Text style={styles.headerSub}>The science, in plain English</Text>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 50 }}>
        {LEARN_SECTIONS.map((section, i) => (
          <AccordionCard
            key={i}
            section={section}
            open={openIdx === i}
            onToggle={() => setOpenIdx(openIdx === i ? null : i)}
          />
        ))}

        {/* Bottom credit */}
        <View style={styles.credit}>
          <Text style={styles.creditText}>🛰️ Powered by NASA PACE · GHRSST MUR · SWOT</Text>
        </View>
      </ScrollView>
    </View>
  );
}

function AccordionCard({
  section,
  open,
  onToggle,
}: {
  section: typeof LEARN_SECTIONS[0];
  open: boolean;
  onToggle: () => void;
}) {
  const heightAnim = useRef(new Animated.Value(open ? 1 : 0)).current;

  React.useEffect(() => {
    Animated.timing(heightAnim, {
      toValue: open ? 1 : 0,
      duration: 280,
      useNativeDriver: false,
    }).start();
  }, [open]);

  return (
    <View style={[styles.card, { borderColor: open ? section.color + "55" : "#0A2540" }]}>
      <TouchableOpacity style={styles.cardHeader} onPress={onToggle} activeOpacity={0.75}>
        <View style={[styles.emojiBox, { backgroundColor: section.color + "22" }]}>
          <Text style={{ fontSize: 22 }}>{section.emoji}</Text>
        </View>
        <Text style={[styles.cardTitle, open && { color: section.color }]}>{section.title}</Text>
        <Ionicons
          name={open ? "chevron-up" : "chevron-down"}
          size={18}
          color={open ? section.color : "#4A7FA5"}
        />
      </TouchableOpacity>

      {open && (
        <View style={styles.cardBody}>
          <Text style={styles.cardDesc}>{section.description}</Text>
          <View style={[styles.divider, { backgroundColor: section.color + "33" }]} />
          {section.keyPoints.map((pt, j) => (
            <View key={j} style={styles.bulletRow}>
              <View style={[styles.bullet, { backgroundColor: section.color }]} />
              <Text style={styles.bulletText}>{pt}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#050D1A" },
  header: { paddingHorizontal: 16, paddingVertical: 14 },
  headerTitle: { color: "#CEE9F7", fontSize: 26, fontWeight: "800" },
  headerSub: { color: "#4A7FA5", fontSize: 14, marginTop: 2 },

  card: {
    backgroundColor: "#071525", borderRadius: 16,
    marginBottom: 10, borderWidth: 1, overflow: "hidden",
  },
  cardHeader: {
    flexDirection: "row", alignItems: "center",
    padding: 16, gap: 12,
  },
  emojiBox: {
    width: 44, height: 44, borderRadius: 12,
    alignItems: "center", justifyContent: "center",
  },
  cardTitle: { flex: 1, color: "#CEE9F7", fontSize: 16, fontWeight: "700" },
  cardBody: { paddingHorizontal: 16, paddingBottom: 18 },
  cardDesc: { color: "#B0D8ED", fontSize: 14, lineHeight: 22, marginBottom: 14 },
  divider: { height: 1, marginBottom: 14 },
  bulletRow: { flexDirection: "row", alignItems: "flex-start", gap: 10, marginBottom: 8 },
  bullet: { width: 6, height: 6, borderRadius: 3, marginTop: 7 },
  bulletText: { color: "#8AB9CE", fontSize: 13, lineHeight: 20, flex: 1 },

  credit: { alignItems: "center", padding: 16 },
  creditText: { color: "#29678A", fontSize: 12 },
});
