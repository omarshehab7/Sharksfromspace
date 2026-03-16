/**
 * SettingsScreen.tsx — User Preferences
 *
 * Allows users to configure:
 * - Push notification preferences (hotspot alerts)
 * - Temperature unit (°C / °F)
 * - Map style (dark / satellite)
 * - About & credits
 */

import React, { useState } from "react";
import { View, Text, ScrollView, Switch, TouchableOpacity } from "react-native";

interface SettingToggleProps {
  label: string;
  description: string;
  value: boolean;
  onToggle: (val: boolean) => void;
}

function SettingToggle({ label, description, value, onToggle }: SettingToggleProps) {
  return (
    <View
      style={{
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        backgroundColor: "#073449",
        borderRadius: 12,
        padding: 16,
        marginBottom: 8,
      }}
    >
      <View style={{ flex: 1, marginRight: 12 }}>
        <Text style={{ color: "#E6F4F9", fontSize: 16, fontWeight: "600" }}>
          {label}
        </Text>
        <Text style={{ color: "#8ECDE5", fontSize: 13, marginTop: 4 }}>
          {description}
        </Text>
      </View>
      <Switch
        value={value}
        onValueChange={onToggle}
        trackColor={{ false: "#0B4D6D", true: "#2E9DCD" }}
        thumbColor={value ? "#E6F4F9" : "#8ECDE5"}
      />
    </View>
  );
}

export default function SettingsScreen() {
  const [notifications, setNotifications] = useState(true);
  const [useCelsius, setUseCelsius] = useState(true);
  const [darkMap, setDarkMap] = useState(true);

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: "#0A1628" }}
      contentContainerStyle={{ padding: 16, paddingTop: 60 }}
    >
      <Text style={{ color: "#E6F4F9", fontSize: 28, fontWeight: "bold", marginBottom: 8 }}>
        Settings
      </Text>
      <Text style={{ color: "#8ECDE5", fontSize: 16, marginBottom: 24 }}>
        Customize your experience
      </Text>

      {/* ---- Notifications ---- */}
      <Text style={{ color: "#5AB5D9", fontSize: 14, fontWeight: "bold", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>
        Notifications
      </Text>
      <SettingToggle
        label="Hotspot Alerts"
        description="Get notified when a new shark hotspot is detected near you"
        value={notifications}
        onToggle={setNotifications}
      />

      {/* ---- Display ---- */}
      <Text style={{ color: "#5AB5D9", fontSize: 14, fontWeight: "bold", marginTop: 20, marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>
        Display
      </Text>
      <SettingToggle
        label="Celsius"
        description="Show temperatures in °C (off = °F)"
        value={useCelsius}
        onToggle={setUseCelsius}
      />
      <SettingToggle
        label="Dark Map"
        description="Use dark map style (off = satellite imagery)"
        value={darkMap}
        onToggle={setDarkMap}
      />

      {/* ---- About ---- */}
      <Text style={{ color: "#5AB5D9", fontSize: 14, fontWeight: "bold", marginTop: 20, marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>
        About
      </Text>
      <View
        style={{
          backgroundColor: "#073449",
          borderRadius: 12,
          padding: 16,
        }}
      >
        <Text style={{ color: "#E6F4F9", fontSize: 16, fontWeight: "bold" }}>
          🦈 Sharks From Space v1.0.0
        </Text>
        <Text style={{ color: "#8ECDE5", marginTop: 8, lineHeight: 20 }}>
          Predicting shark activity using NASA satellite data and machine learning.
          Ocean data provided by NASA Earthdata. Built with ❤️ for ocean education.
        </Text>
      </View>
    </ScrollView>
  );
}
