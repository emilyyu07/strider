import type { Coordinates, RouteResponse } from '../types'
import PromptInput from './PromptInput'
import RouteDetails from './RouteDetails'

interface SidebarProps {
  currentLocation: Coordinates | null
  route: RouteResponse | null
  trackingEnabled: boolean
  trackingStatus: 'requesting' | 'active' | 'paused' | 'unsupported' | 'denied' | 'error'
  lastLocationUpdateMs: number | null
  autoRerouteEnabled: boolean
  autoRerouteDriftM: number
  loading: boolean
  error: string | null
  canRegenerate: boolean
  onToggleTracking: () => void
  onToggleAutoReroute: () => void
  onPromptSubmit: (prompt: string) => void
  onRegenerate: () => void
  onReset: () => void
}

export default function Sidebar({
  currentLocation,
  route,
  trackingEnabled,
  trackingStatus,
  lastLocationUpdateMs,
  autoRerouteEnabled,
  autoRerouteDriftM,
  loading,
  error,
  canRegenerate,
  onToggleTracking,
  onToggleAutoReroute,
  onPromptSubmit,
  onRegenerate,
  onReset,
}: SidebarProps) {
  const trackingTextMap = {
    requesting: 'Locating...',
    active: 'Live tracking active',
    paused: 'Tracking paused',
    unsupported: 'Geolocation unsupported (fallback active)',
    denied: 'Location permission denied (fallback active)',
    error: 'Location signal error (fallback active)',
  } as const

  const lastUpdated =
    lastLocationUpdateMs !== null ? new Date(lastLocationUpdateMs).toLocaleTimeString() : 'No fix yet'

  return (
    <aside className="sidebar">
      <h1>Strider</h1>
      <p className="subtitle">Semantic running route assistant</p>

      <div className="section">
        <h3>Current location</h3>
        <p>
          {currentLocation
            ? `${currentLocation.lat.toFixed(5)}, ${currentLocation.lng.toFixed(5)}`
            : 'Resolving GPS location…'}
        </p>
        <p className="status">{trackingTextMap[trackingStatus]}</p>
        <p className="status">Last update: {lastUpdated}</p>
        <button onClick={onToggleTracking} disabled={loading}>
          {trackingEnabled ? 'Pause tracking' : 'Resume tracking'}
        </button>
      </div>

      <div className="section">
        <h3>Auto-reroute</h3>
        <label className="toggle-row">
          <input
            type="checkbox"
            checked={autoRerouteEnabled}
            onChange={onToggleAutoReroute}
            disabled={!canRegenerate || loading}
          />
          <span>Regenerate if drift exceeds {autoRerouteDriftM}m</span>
        </label>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="section">
        <PromptInput onSubmit={onPromptSubmit} loading={loading} disabled={!currentLocation} />
      </div>

      <div className="section">
        <button onClick={onRegenerate} disabled={!canRegenerate || loading}>
          Regenerate route
        </button>
        <button onClick={onReset} disabled={loading}>
          Clear route
        </button>
      </div>

      <div className="section">
        <RouteDetails route={route} />
      </div>
    </aside>
  )
}
