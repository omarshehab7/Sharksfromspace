import { registerRootComponent } from "expo";
import MapboxGL from "@rnmapbox/maps";
import App from "./App";

// Initialize Mapbox with your public access token
MapboxGL.setAccessToken(process.env.EXPO_PUBLIC_MAPBOX_TOKEN)
// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately.
registerRootComponent(App);
