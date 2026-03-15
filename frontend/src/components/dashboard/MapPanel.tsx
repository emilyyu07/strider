import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import type { Coordinates, RouteResponse } from '../../types'
import { toMapLibreLineCoordinates } from '../../utils/coordinates'
import './MapPanel.css'

const DEFAULT_CENTER: [number, number] = [-80.5204, 43.4643]

interface MapPanelProps {
  locationName: string
  currentLocation: Coordinates
  route: RouteResponse | null
}

function toPath(points: [number, number][]): string {
  if (points.length === 0) {
    return ''
  }
  return points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'} ${x} ${y}`).join(' ')
}

export default function MapPanel({ locationName, currentLocation, route }: MapPanelProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const [mapReady, setMapReady] = useState(false)
  const [mapSize, setMapSize] = useState({ width: 0, height: 0 })
  const [routePixels, setRoutePixels] = useState<[number, number][]>([])

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return
    }
    mapRef.current = new maplibregl.Map({
      container: mapContainerRef.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: DEFAULT_CENTER,
      zoom: 12.8,
    })
    mapRef.current.on('load', () => {
      setMapReady(true)
      if (mapContainerRef.current) {
        setMapSize({
          width: mapContainerRef.current.clientWidth,
          height: mapContainerRef.current.clientHeight,
        })
      }
    })
    mapRef.current.addControl(new maplibregl.NavigationControl(), 'top-right')

    return () => {
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!mapRef.current || !mapReady) {
      return
    }
    if (!route) {
      mapRef.current.flyTo({ center: [currentLocation.lng, currentLocation.lat], zoom: 13.2, duration: 700 })
    }
  }, [currentLocation, mapReady, route])

  useEffect(() => {
    if (!mapRef.current || !mapReady || !route || route.route_polyline.length === 0) {
      setRoutePixels([])
      return
    }
    const map = mapRef.current
    const coords = toMapLibreLineCoordinates(route.route_polyline)
    const bounds = coords.reduce((acc, point) => acc.extend(point), new maplibregl.LngLatBounds(coords[0], coords[0]))
    map.fitBounds(bounds, { padding: 54, duration: 850 })

    const syncRoutePixels = () => {
      if (!mapContainerRef.current || !route) {
        return
      }
      setRoutePixels(
        toMapLibreLineCoordinates(route.route_polyline).map((coord) => {
          const p = map.project(coord)
          return [p.x, p.y]
        }),
      )
      setMapSize({
        width: mapContainerRef.current.clientWidth,
        height: mapContainerRef.current.clientHeight,
      })
    }

    syncRoutePixels()
    map.on('move', syncRoutePixels)
    map.on('resize', syncRoutePixels)
    return () => {
      map.off('move', syncRoutePixels)
      map.off('resize', syncRoutePixels)
    }
  }, [mapReady, route])

  const routePath = useMemo(() => toPath(routePixels), [routePixels])
  const midpointIndexes = useMemo(() => {
    if (routePixels.length < 4) {
      return []
    }
    return [Math.round(routePixels.length * 0.4), Math.round(routePixels.length * 0.75)]
  }, [routePixels.length])

  return (
    <div className="map-area">
      <div className="map-live" ref={mapContainerRef} />
      <div className="dot-grid" />
      <div className="scan" />

      <svg className="route-svg" width={mapSize.width} height={mapSize.height}>
        {routePath && (
          <>
            <path d={routePath} className="route-ghost" />
            <path d={routePath} className="route-main" />
          </>
        )}
        {routePixels[0] && (
          <g>
            <circle cx={routePixels[0][0]} cy={routePixels[0][1]} r="18" className="route-start-outer" />
            <circle cx={routePixels[0][0]} cy={routePixels[0][1]} r="10" className="route-start-ring" />
            <circle cx={routePixels[0][0]} cy={routePixels[0][1]} r="4" className="route-start-dot" />
          </g>
        )}
        {routePixels[routePixels.length - 1] && (
          <g>
            <circle cx={routePixels[routePixels.length - 1][0]} cy={routePixels[routePixels.length - 1][1]} r="12" className="route-start-ring" />
            <circle cx={routePixels[routePixels.length - 1][0]} cy={routePixels[routePixels.length - 1][1]} r="4" className="route-start-dot" />
          </g>
        )}
        {midpointIndexes.map((idx, i) => {
          const p = routePixels[idx]
          if (!p || !route) {
            return null
          }
          return (
            <g key={`${idx}-${i}`}>
              <circle cx={p[0]} cy={p[1]} r="5" className="waypoint-outer" />
              <circle cx={p[0]} cy={p[1]} r="2" className="waypoint-inner" />
              <text x={p[0] + 10} y={p[1] - 5} className="waypoint-text">
                {`${((route.distance_m * (idx / routePixels.length)) / 1000).toFixed(1)}KM`}
              </text>
            </g>
          )
        })}
        <path d="M 16,16 L 16,32 M 16,16 L 32,16" className="corner-path" />
        <path d="M 584,16 L 584,32 M 584,16 L 568,16" className="corner-path" />
        <path d="M 16,364 L 16,348 M 16,364 L 32,364" className="corner-path" />
        <path d="M 584,364 L 584,348 M 584,364 L 568,364" className="corner-path" />
      </svg>

      <div className="hud hud-tl">
        <div className="hud-label">CURRENT LOCATION</div>
        <div className="hud-value bright">{locationName}</div>
        <div className="hud-coords">{`${Math.abs(currentLocation.lat).toFixed(4)}° ${currentLocation.lat >= 0 ? 'N' : 'S'} · ${Math.abs(currentLocation.lng).toFixed(4)}° ${currentLocation.lng >= 0 ? 'E' : 'W'}`}</div>
      </div>

      <div className="hud hud-br">
        <div className="hud-label">ROUTE DISTANCE</div>
        <div className="hud-value bright">{route ? `${(route.distance_m / 1000).toFixed(1)} KM` : '--'}</div>
        <div className="hud-label est-label">EST. DURATION</div>
        <div className="hud-value bright">{route ? `${Math.round(route.duration_estimate_s / 60)} MIN` : '--'}</div>
      </div>

      <div className="hud hud-bl">
        <div className="hud-label">LOCKED</div>
        <div className="hud-value">{route ? 'LOOP · ORIGIN ANCHORED' : '--'}</div>
      </div>
    </div>
  )
}

