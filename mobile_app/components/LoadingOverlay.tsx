/**
 * LoadingOverlay.tsx — Full-screen loading with ocean message
 */

import React, { useEffect, useRef } from "react";
import { View, Text, Animated, Easing, StyleSheet } from "react-native";

interface Props {
  message?: string;
}

export default function LoadingOverlay({ message = "Scanning the ocean..." }: Props) {
  const spin = useRef(new Animated.Value(0)).current;
  const pulse = useRef(new Animated.Value(0.95)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(spin, { toValue: 1, duration: 3000, easing: Easing.linear, useNativeDriver: true })
    ).start();
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1.1, duration: 1200, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0.95, duration: 1200, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const rotate = spin.interpolate({ inputRange: [0, 1], outputRange: ["0deg", "360deg"] });

  return (
    <View style={styles.container}>
      <Animated.Text style={[styles.emoji, { transform: [{ rotate }, { scale: pulse }] }]}>
        🛰️
      </Animated.Text>
      <Text style={styles.title}>Scanning from Space</Text>
      <Text style={styles.message}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1, backgroundColor: "#050D1A",
    alignItems: "center", justifyContent: "center",
  },
  emoji: { fontSize: 56, marginBottom: 20 },
  title: { color: "#CEE9F7", fontSize: 20, fontWeight: "700", marginBottom: 8 },
  message: { color: "#4A7FA5", fontSize: 14 },
});
