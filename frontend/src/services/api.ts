/**
 * API service for backend communication
 */

import axios from "axios";
import type { RouteRequest, GeoJSONResponse } from "../types";

// Base URL for backend API
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Create axios instance with defaults
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 second timeout
});

/**
 * Health check
 */
export const healthCheck = async () => {
  const response = await apiClient.get("/health");
  return response.data;
};

/**
 * Plan a route
 */
export const planRoute = async (
  request: RouteRequest,
): Promise<GeoJSONResponse> => {
  const response = await apiClient.post<GeoJSONResponse>(
    "/plan-route",
    request,
  );
  return response.data;
};

/**
 * Analyze prompt only (for testing)
 */
export const analyzePrompt = async (prompt: string) => {
  const response = await apiClient.post("/analyze-prompt", { prompt });
  return response.data;
};

/**
 * Get sample coordinates
 */
export const getSampleCoordinates = async () => {
  const response = await apiClient.get("/test-coordinates");
  return response.data;
};

export default {
  healthCheck,
  planRoute,
  analyzePrompt,
  getSampleCoordinates,
};
