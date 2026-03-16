/**
 * SharkFactCard.tsx — Shark Species Fact Card
 *
 * Displays a brief profile card for a shark species,
 * including a fun fact and preferred ocean conditions.
 */

import React from "react";
import { View, Text } from "react-native";

interface Props {
  speciesName: string;
}

// Species database — expand as needed
const SPECIES_DATA: Record<string, { emoji: string; fact: string; habitat: string }> = {
  "Great White": {
    emoji: "🦈",
    fact: "Great white sharks can detect a single drop of blood in 25 gallons of water.",
    habitat: "Temperate coastal waters, 12-24°C",
  },
  "Tiger Shark": {
    emoji: "🐅",
    fact: "Tiger sharks are known as the 'garbage cans of the sea' due to their varied diet.",
    habitat: "Warm tropical waters, 20-30°C",
  },
  "Hammerhead": {
    emoji: "🔨",
    fact: "Hammerheads' wide-set eyes give them a 360-degree field of vision.",
    habitat: "Warm coastal waters, 18-28°C",
  },
  "Bull Shark": {
    emoji: "🐂",
    fact: "Bull sharks can survive in both salt and freshwater environments.",
    habitat: "Warm shallow waters, coastal and riverine",
  },
  "Whale Shark": {
    emoji: "🐋",
    fact: "Despite being the largest fish, whale sharks are gentle filter feeders.",
    habitat: "Tropical open waters, 21-30°C",
  },
};

const DEFAULT_SPECIES = {
  emoji: "🦈",
  fact: "Sharks have been around for over 400 million years — older than dinosaurs!",
  habitat: "Various ocean environments",
};

export default function SharkFactCard({ speciesName }: Props) {
  const species = SPECIES_DATA[speciesName] || DEFAULT_SPECIES;

  return (
    <View
      style={{
        backgroundColor: "#073449",
        borderRadius: 12,
        padding: 16,
        marginBottom: 8,
        flexDirection: "row",
      }}
    >
      <Text style={{ fontSize: 32, marginRight: 12 }}>{species.emoji}</Text>
      <View style={{ flex: 1 }}>
        <Text style={{ color: "#E6F4F9", fontSize: 16, fontWeight: "bold" }}>
          {speciesName}
        </Text>
        <Text style={{ color: "#C2E5F1", fontSize: 13, marginTop: 4, lineHeight: 18 }}>
          {species.fact}
        </Text>
        <Text style={{ color: "#5AB5D9", fontSize: 12, marginTop: 4 }}>
          🌊 {species.habitat}
        </Text>
      </View>
    </View>
  );
}
