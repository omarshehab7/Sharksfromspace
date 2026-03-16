/**
 * apiClient.ts — Axios HTTP client for the Sharks From Space API
 */

import axios from "axios";

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: { "Content-Type": "application/json" },
});

// Response interceptor — log errors in dev
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (__DEV__) {
      console.warn("[API Error]", error?.response?.status, error?.config?.url, error?.message);
    }
    return Promise.reject(error);
  }
);
