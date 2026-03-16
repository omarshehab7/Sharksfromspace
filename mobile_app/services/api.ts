/**
 * api.ts — Backend API Client
 *
 * Configured Axios instance for communicating with the FastAPI backend.
 * All API hooks (useHotspots, useOceanData) use this client.
 *
 * Configuration:
 * - Base URL is set via environment variable or defaults to localhost.
 * - Request/response interceptors for error handling and logging.
 */

import axios from "axios";
import Constants from "expo-constants";

// Base URL — configurable via Expo extra config or fallback to localhost
const BASE_URL =
  Constants.expoConfig?.extra?.apiBaseUrl || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15000, // 15 second timeout
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ---- Request Interceptor ----
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token here if needed in the future
    // config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ---- Response Interceptor ----
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error(
        `API Error [${error.response.status}]:`,
        error.response.data?.detail || error.message
      );
    } else if (error.request) {
      // No response received
      console.error("API Error: No response from server. Is the backend running?");
    } else {
      console.error("API Error:", error.message);
    }
    return Promise.reject(error);
  }
);
