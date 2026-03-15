import type { RefObject } from 'react'

interface RouteMapPanelProps {
  mapContainerRef: RefObject<HTMLDivElement | null>
  mapSize: { width: number; height: number }
  routePath: string
  routePixels: [number, number][]
  waypointIndexes: number[]
  routeDistanceM: number | null
  routeDistanceLabel: string
  durationLabel: string
  routeReady: boolean
}

export default function RouteMapPanel({
  mapContainerRef,
  mapSize,
  routePath,
  routePixels,
  waypointIndexes,
  routeDistanceM,
  routeDistanceLabel,
  durationLabel,
  routeReady,
}: RouteMapPanelProps) {
  return (
    <div className="map-row">
      <div ref={mapContainerRef} className="map-canvas" />
      <div className="overlay overlay-dot-grid" />
      <div className="overlay overlay-scanlines" />

      <svg className="route-overlay" width={mapSize.width} height={mapSize.height}>
        {routePath && (
          <>
            <path d={routePath} className="route-glow" />
            <path d={routePath} className="route-main" />
          </>
        )}
        {waypointIndexes.map((index) => {
          const point = routePixels[index]
          if (!point) {
            return null
          }
          const labelKm = routeDistanceM !== null ? ((routeDistanceM * ((index + 1) / routePixels.length)) / 1000).toFixed(1) : '--'
          return (
            <g key={`${point[0]}-${point[1]}-${index}`}>
              <circle cx={point[0]} cy={point[1]} r="5" className="waypoint-ring" />
              <circle cx={point[0]} cy={point[1]} r="2" className="waypoint-dot" />
              <text x={point[0] + 8} y={point[1] - 8} className="waypoint-label">{`${labelKm}K`}</text>
            </g>
          )
        })}
        {routePixels[0] && (
          <g>
            <circle cx={routePixels[0][0]} cy={routePixels[0][1]} r="8" className="pin-ring" />
            <circle cx={routePixels[0][0]} cy={routePixels[0][1]} r="4" className="pin-core" />
            <line
              x1={routePixels[0][0] - 10}
              y1={routePixels[0][1]}
              x2={routePixels[0][0] + 10}
              y2={routePixels[0][1]}
              className="pin-crosshair"
            />
            <line
              x1={routePixels[0][0]}
              y1={routePixels[0][1] - 10}
              x2={routePixels[0][0]}
              y2={routePixels[0][1] + 10}
              className="pin-crosshair"
            />
          </g>
        )}
        {routePixels[routePixels.length - 1] && (
          <g>
            <circle cx={routePixels[routePixels.length - 1][0]} cy={routePixels[routePixels.length - 1][1]} r="8" className="pin-ring" />
            <circle cx={routePixels[routePixels.length - 1][0]} cy={routePixels[routePixels.length - 1][1]} r="4" className="pin-core" />
          </g>
        )}
      </svg>

      <div className="map-corners">
        <span className="map-corner tl" />
        <span className="map-corner tr" />
        <span className="map-corner bl" />
        <span className="map-corner br" />
      </div>

      <div className="hud hud-right">
        <div className="hud-row">
          <span className="hud-label">ROUTE DISTANCE</span>
          <span className="hud-value">{routeDistanceLabel}</span>
        </div>
        <div className="hud-row">
          <span className="hud-label">EST. DURATION</span>
          <span className="hud-value">{durationLabel}</span>
        </div>
      </div>

      <div className="hud hud-left">
        <span className="hud-label">LOCKED</span>
        <span className="hud-value">{routeReady ? 'LOOP · ORIGIN ANCHORED' : '--'}</span>
      </div>
    </div>
  )
}

