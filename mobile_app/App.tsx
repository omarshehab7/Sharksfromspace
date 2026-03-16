/**
 * App.tsx — Root Application Component
 *
 * 4-tab navigation:
 *   🗺️ Explore   — Interactive map with hotspot markers
 *   🦈 Species   — Species Explorer
 *   📡 Tracker   — Shark Tag Simulation
 *   📚 Learn     — Educational content
 */

import "./global.css";
import React from "react";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { View } from "react-native";

// Screens
import HomeScreen from "./screens/HomeScreen";
import HotspotDetailScreen from "./screens/HotspotDetailScreen";
import SpeciesExplorerScreen from "./screens/SpeciesExplorerScreen";
import SharkTrackerScreen from "./screens/SharkTrackerScreen";
import LearnScreen from "./screens/LearnScreen";

// ---- Navigation Setup ----

const Tab = createBottomTabNavigator();
const MapStack = createNativeStackNavigator();

function MapStackNavigator() {
  return (
    <MapStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: "#050D1A" },
        headerTintColor: "#CEE9F7",
        headerTitleStyle: { fontWeight: "bold" },
      }}
    >
      <MapStack.Screen
        name="Map"
        component={HomeScreen}
        options={{ headerShown: false }}
      />
      <MapStack.Screen
        name="HotspotDetail"
        component={HotspotDetailScreen}
        options={{ title: "Hotspot Details", headerBackTitle: "Map" }}
      />
    </MapStack.Navigator>
  );
}

// ---- Query Client ----

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 min
      retry: 2,
    },
  },
});

// ---- App Component ----

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer>
        <StatusBar style="light" />
        <Tab.Navigator
          screenOptions={({ route }) => ({
            headerShown: false,
            tabBarStyle: {
              backgroundColor: "#050D1A",
              borderTopColor: "#0A2540",
              borderTopWidth: 1,
              paddingBottom: 10,
              paddingTop: 8,
              height: 68,
            },
            tabBarActiveTintColor: "#29ABE2",
            tabBarInactiveTintColor: "#4A7FA5",
            tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
            tabBarIcon: ({ focused, color, size }) => {
              const s = focused ? size : size - 2;
              if (route.name === "Explore")
                return <Ionicons name={focused ? "map" : "map-outline"} size={s} color={color} />;
              if (route.name === "Species")
                return <Ionicons name={focused ? "fish" : "fish-outline"} size={s} color={color} />;
              if (route.name === "Tracker")
                return <Ionicons name={focused ? "radio" : "radio-outline"} size={s} color={color} />;
              if (route.name === "Learn")
                return <Ionicons name={focused ? "book" : "book-outline"} size={s} color={color} />;
              return <Ionicons name="ellipse" size={s} color={color} />;
            },
          })}
        >
          <Tab.Screen name="Explore" component={MapStackNavigator} />
          <Tab.Screen name="Species" component={SpeciesExplorerScreen} />
          <Tab.Screen name="Tracker" component={SharkTrackerScreen} />
          <Tab.Screen name="Learn" component={LearnScreen} />
        </Tab.Navigator>
      </NavigationContainer>
    </QueryClientProvider>
  );
}
