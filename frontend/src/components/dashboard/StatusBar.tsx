import './StatusBar.css'

interface StatusBarProps {
  gpsLocked: boolean
  routeReady: boolean
  coachActive: boolean
  weatherLive: boolean
  cityLabel: string
}

function Dot({ color, on }: { color: string; on: boolean }) {
  return <div className="status-dot-mini" style={{ background: color, opacity: on ? 1 : 0.3 }} />
}

export default function StatusBar({
  gpsLocked,
  routeReady,
  coachActive,
  weatherLive,
  cityLabel,
}: StatusBarProps) {
  return (
    <div className="status-bar">
      <div className="status-left">
        <div className="status-item"><Dot color="#38bdf8" on={gpsLocked} />GPS LOCKED</div>
        <div className="status-item"><Dot color="#10b981" on={routeReady} />ROUTE READY</div>
        <div className="status-item"><Dot color="#8b5cf6" on={coachActive} />COACH ACTIVE</div>
        <div className="status-item"><Dot color="#f59e0b" on={weatherLive} />WEATHER LIVE</div>
      </div>
      <div className="status-item sys-label">{`SYS · STRIDER v0.1 · ${cityLabel}`}</div>
    </div>
  )
}

