import { registerRootComponent } from "expo";
import MapboxGL from "@rnmapbox/maps";
import App from "./App";

// Initialize Mapbox with your public access token
MapboxGL.setAccessToken(process.env.EXPO_PUBLIC_MAPBOX_TOKEN ?? "pk.eyJ1Ijoib21hcm1vaGFtZWQyNiIsImEiOiJjbW1zOGt3bmwxZWI1MnByMDNnOHlxaHM2In0.NCPTvkh9j7iY6tXwJ8fc2w");

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately.
registerRootComponent(App);
