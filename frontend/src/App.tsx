import { useCallback, useEffect, useRef, useState } from 'react'
import axios from 'axios'

import './App.css'
import Map from './components/Map'
import Sidebar from './components/Sidebar'
import { generateRoute, regenerateRoute } from './services/api'
import type { Coordinates, LLMRouteParameters, RouteResponse } from './types'

const DEFAULT_LOCATION: Coordinates = { lat: 43.5448, lng: -80.2482 }
const LOCATION_THROTTLE_MS = 2000
const LOCATION_MIN_MOVE_M = 8
const AUTO_REROUTE_DRIFT_M = 40
const AUTO_REROUTE_COOLDOWN_MS = 15000

type TrackingStatus = 'requesting' | 'active' | 'paused' | 'unsupported' | 'denied' | 'error'

function toRadians(value: number): number {
  return (value * Math.PI) / 180
}

function distanceMeters(a: Coordinates, b: Coordinates): number {
  const earthRadiusM = 6_371_000
  const dLat = toRadians(b.lat - a.lat)
  const dLng = toRadians(b.lng - a.lng)
  const lat1 = toRadians(a.lat)
  const lat2 = toRadians(b.lat)
  const haversine =
    Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2
  const angularDistance = 2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine))
  return earthRadiusM * angularDistance
}

export default function App() {
  const [currentLocation, setCurrentLocation] = useState<Coordinates | null>(null)
  const [route, setRoute] = useState<RouteResponse | null>(null)
  const [parameters, setParameters] = useState<LLMRouteParameters | null>(null)
  const [trackingEnabled, setTrackingEnabled] = useState(true)
  const [autoRerouteEnabled, setAutoRerouteEnabled] = useState(false)
  const [trackingStatus, setTrackingStatus] = useState<TrackingStatus>('requesting')
  const [lastLocationUpdateMs, setLastLocationUpdateMs] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const lastAcceptedAtRef = useRef(0)
  const lastAcceptedLocationRef = useRef<Coordinates | null>(null)
  const lastAutoRerouteAtRef = useRef(0)

  useEffect(() => {
    if (!trackingEnabled) {
      setTrackingStatus('paused')
      return
    }

    if (!navigator.geolocation) {
      setCurrentLocation(DEFAULT_LOCATION)
      setTrackingStatus('unsupported')
      setLastLocationUpdateMs(Date.now())
      return
    }
    setTrackingStatus('requesting')

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const nextLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        }
        const now = Date.now()
        const previous = lastAcceptedLocationRef.current
        const movedMeters = previous ? distanceMeters(previous, nextLocation) : Number.POSITIVE_INFINITY
        if (now - lastAcceptedAtRef.current < LOCATION_THROTTLE_MS && movedMeters < LOCATION_MIN_MOVE_M) {
          return
        }

        lastAcceptedAtRef.current = now
        lastAcceptedLocationRef.current = nextLocation
        setCurrentLocation(nextLocation)
        setTrackingStatus('active')
        setLastLocationUpdateMs(now)
      },
      (geoError) => {
        if (geoError.code === geoError.PERMISSION_DENIED) {
          setTrackingStatus('denied')
        } else {
          setTrackingStatus('error')
        }
        setCurrentLocation((previous) => previous ?? DEFAULT_LOCATION)
        setLastLocationUpdateMs((previous) => previous ?? Date.now())
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 1000,
      },
    )

    return () => {
      navigator.geolocation.clearWatch(watchId)
    }
  }, [trackingEnabled])

  const handleGenerateRoute = async (prompt: string) => {
    if (!currentLocation) {
      setError('Current location is not available yet.')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const nextRoute = await generateRoute({
        prompt,
        current_location: currentLocation,
      })
      setRoute(nextRoute)
      setParameters(nextRoute.parameters)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? 'Failed to generate route.')
      } else {
        setError('Failed to generate route.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRegenerateRoute = useCallback(async () => {
    if (!currentLocation || !parameters) {
      return
    }
    if (loading) {
      return
    }
    setLoading(true)
    setError(null)
    try {
      const nextRoute = await regenerateRoute({
        previous_parameters: parameters,
        current_location: currentLocation,
      })
      setRoute(nextRoute)
      setParameters(nextRoute.parameters)
    } catch {
      setError('Failed to regenerate route.')
    } finally {
      setLoading(false)
    }
  }, [currentLocation, parameters, loading])

  useEffect(() => {
    if (!autoRerouteEnabled || !trackingEnabled || !currentLocation || !route || loading) {
      return
    }
    if (route.route.length === 0) {
      return
    }

    const [startLat, startLng] = route.route[0]
    const routeStart = { lat: startLat, lng: startLng }
    const driftMeters = distanceMeters(currentLocation, routeStart)
    if (driftMeters <= AUTO_REROUTE_DRIFT_M) {
      return
    }

    const now = Date.now()
    if (now - lastAutoRerouteAtRef.current < AUTO_REROUTE_COOLDOWN_MS) {
      return
    }
    lastAutoRerouteAtRef.current = now
    void handleRegenerateRoute()
  }, [autoRerouteEnabled, trackingEnabled, currentLocation, route, loading, handleRegenerateRoute])

  const handleTrackingToggle = () => {
    setTrackingEnabled((previous) => !previous)
  }

  const handleAutoRerouteToggle = () => {
    setAutoRerouteEnabled((previous) => !previous)
  }

  const handleReset = () => {
    setRoute(null)
    setParameters(null)
    setError(null)
  }

  return (
    <div className="app-shell">
      <Sidebar
        currentLocation={currentLocation}
        route={route}
        trackingEnabled={trackingEnabled}
        trackingStatus={trackingStatus}
        lastLocationUpdateMs={lastLocationUpdateMs}
        autoRerouteEnabled={autoRerouteEnabled}
        autoRerouteDriftM={AUTO_REROUTE_DRIFT_M}
        loading={loading}
        error={error}
        canRegenerate={Boolean(parameters)}
        onToggleTracking={handleTrackingToggle}
        onToggleAutoReroute={handleAutoRerouteToggle}
        onPromptSubmit={handleGenerateRoute}
        onRegenerate={handleRegenerateRoute}
        onReset={handleReset}
      />
      <div className="map-shell">
        <Map currentLocation={currentLocation} route={route} />
      </div>
    </div>
  )
}
