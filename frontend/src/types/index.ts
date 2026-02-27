/**
 * Type definitions for Strider frontend
 */

// Coordinates
export interface Coordinates {
  lng: number;
  lat: number;
}

// Route request to backend
export interface RouteRequest {
  prompt: string;
  start_lon: number;
  start_lat: number;
  end_lon?: number;
  end_lat?: number;
  target_distance_km?: number;
}

// GeoJSON types
export interface GeoJSONGeometry {
  type: string;
  coordinates: number[][] | number[][][];
}

export interface RouteProperties {
  distance_km: number;
  distance_m: number;
  segment_count: number;
  lit_segments: number;
  scenic_segments: number;
  prompt: string;
  llm_preferences: Record<string, number>;
  llm_reasoning: string;
  start_node: number;
  end_node: number;
  phase: string;
  performance?: {
    llm_time_s: number;
    routing_time_s: number;
    total_time_s: number;
  };
  segments?: RouteSegment[];
}

export interface RouteSegment {
  seq: number;
  type: string;
  name: string;
  length_m: number;
  lit: boolean;
  scenic_score: number;
}

export interface GeoJSONFeature {
  type: string;
  geometry: GeoJSONGeometry;
  properties: RouteProperties;
}

export interface GeoJSONResponse {
  type: string;
  features: GeoJSONFeature[];
}

// App state
export interface MapMarker {
  type: "start" | "end";
  coordinates: Coordinates;
}

export interface AppState {
  startPoint: Coordinates | null;
  endPoint: Coordinates | null;
  prompt: string;
  route: GeoJSONResponse | null;
  loading: boolean;
  error: string | null;
}
