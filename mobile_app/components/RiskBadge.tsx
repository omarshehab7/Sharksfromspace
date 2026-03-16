/**
 * RiskBadge.tsx — Color-coded activity level badge
 */

import React from "react";
import { View, Text, StyleSheet } from "react-native";

interface Props {
  level: "low" | "medium" | "high";
  size?: "small" | "large";
}

const CONFIG = {
  low:    { bg: "#052010", border: "#22C55E", text: "#22C55E", label: "Low" },
  medium: { bg: "#1E1000", border: "#F59E0B", text: "#F59E0B", label: "Moderate" },
  high:   { bg: "#1E0505", border: "#EF4444", text: "#EF4444", label: "High" },
};

export default function RiskBadge({ level, size = "small" }: Props) {
  const c = CONFIG[level];
  const large = size === "large";
  return (
    <View style={[styles.badge, { backgroundColor: c.bg, borderColor: c.border }, large && styles.badgeLarge]}>
      <Text style={[styles.text, { color: c.text }, large && styles.textLarge]}>
        {level === "high" ? "⚠️ " : level === "medium" ? "🔶 " : "✅ "}{c.label} Activity
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { borderRadius: 20, paddingHorizontal: 12, paddingVertical: 5, borderWidth: 1 },
  badgeLarge: { paddingHorizontal: 18, paddingVertical: 9 },
  text: { fontSize: 12, fontWeight: "700" },
  textLarge: { fontSize: 16 },
});
