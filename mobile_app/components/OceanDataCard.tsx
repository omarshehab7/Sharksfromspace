/**
 * OceanDataCard.tsx — Small stat card for ocean parameters
 */

import React from "react";
import { View, Text, StyleSheet } from "react-native";

interface Props {
  icon: string;
  label: string;
  value: string;
  note?: string;
}

export default function OceanDataCard({ icon, label, value, note }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.icon}>{icon}</Text>
      <Text style={styles.value}>{value}</Text>
      <Text style={styles.label}>{label}</Text>
      {note && <Text style={styles.note}>{note}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#071525", borderRadius: 14,
    padding: 14, minWidth: 110, flex: 1,
    borderWidth: 1, borderColor: "#0A2540",
    alignItems: "center",
  },
  icon: { fontSize: 24, marginBottom: 6 },
  value: { color: "#CEE9F7", fontSize: 17, fontWeight: "700" },
  label: { color: "#4A7FA5", fontSize: 11, marginTop: 4, textAlign: "center" },
  note: { color: "#29678A", fontSize: 10, marginTop: 3, textAlign: "center" },
});
