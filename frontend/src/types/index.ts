export interface Coordinates {
  lat: number
  lng: number
}

export interface LLMRouteParameters {
  distance_m: number
  preferences: string[]
  start_lat: number
  start_lng: number
}

export interface GenerateRouteRequest {
  prompt: string
  distance_m: number
  preferences: string[]
  current_location: Coordinates
}

export interface RegenerateRouteRequest {
  previous_parameters: LLMRouteParameters
  current_location: Coordinates
}

export interface RouteResponse {
  route_polyline: [number, number][]
  distance_m: number
  preferences: string[]
  duration_estimate_s: number
  coach_message: string
  parameters: LLMRouteParameters
}
