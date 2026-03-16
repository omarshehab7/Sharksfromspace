/**
 * SharkHotspotMarker.tsx — Custom Map Marker
 *
 * A Mapbox point annotation that displays a shark icon on the map.
 * Color-coded by risk level:
 *   - Green: low risk
 *   - Orange: medium risk
 *   - Red: high risk
 */

import React from "react";
import { View, Text, TouchableOpacity } from "react-native";
import MapboxGL from "@rnmapbox/maps";

interface Hotspot {
  id: string;
  latitude: number;
  longitude: number;
  risk_level: "low" | "medium" | "high";
}

interface Props {
  hotspot: Hotspot;
  onPress: () => void;
}

const RISK_COLORS = {
  low: "#06D6A0",
  medium: "#FF6B35",
  high: "#E63946",
};

export default function SharkHotspotMarker({ hotspot, onPress }: Props) {
  const color = RISK_COLORS[hotspot.risk_level];

  return (
    <MapboxGL.PointAnnotation
      id={`hotspot-${hotspot.id}`}
      coordinate={[hotspot.longitude, hotspot.latitude]}
      onSelected={onPress}
    >
      <TouchableOpacity
        onPress={onPress}
        style={{
          width: 40,
          height: 40,
          borderRadius: 20,
          backgroundColor: color,
          justifyContent: "center",
          alignItems: "center",
          borderWidth: 3,
          borderColor: "#0A1628",
          shadowColor: color,
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.6,
          shadowRadius: 6,
          elevation: 8,
        }}
      >
        <Text style={{ fontSize: 20 }}>🦈</Text>
      </TouchableOpacity>
    </MapboxGL.PointAnnotation>
  );
}
