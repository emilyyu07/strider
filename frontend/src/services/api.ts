/*API client */

import axios from "axios";
import type {
  GenerateRouteRequest,
  RegenerateRouteRequest,
  RouteResponse,
  CoverageCheckResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 60000, // Increased to 60 seconds for LLM processing
});

export const generateRoute = async (
  request: GenerateRouteRequest,
): Promise<RouteResponse> => {
  console.log('[API] Sending generateRoute request:', request);
  console.log('[API] Using base URL:', API_BASE_URL);
  try {
    const response = await apiClient.post<RouteResponse>(
      "/api/route/generate",
      request,
    );
    console.log('[API] Received response:', response.data);
    return response.data;
  } catch (error) {
    console.error('[API] Request failed:', error);
    throw error;
  }
};

export const regenerateRoute = async (
  request: RegenerateRouteRequest,
): Promise<RouteResponse> => {
  const response = await apiClient.post<RouteResponse>(
    "/api/route/regenerate",
    request,
  );
  return response.data;
};

export const checkCoverage = async (
  lat: number,
  lng: number,
): Promise<CoverageCheckResponse> => {
  const response = await apiClient.post<CoverageCheckResponse>(
    "/api/coverage/check",
    { lat, lng },
  );
  return response.data;
};
