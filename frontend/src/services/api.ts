import axios from 'axios'
import type { GenerateRouteRequest, RegenerateRouteRequest, RouteResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

export const generateRoute = async (request: GenerateRouteRequest): Promise<RouteResponse> => {
  const response = await apiClient.post<RouteResponse>('/api/route/generate', request)
  return response.data
}

export const regenerateRoute = async (request: RegenerateRouteRequest): Promise<RouteResponse> => {
  const response = await apiClient.post<RouteResponse>('/api/route/regenerate', request)
  return response.data
}
