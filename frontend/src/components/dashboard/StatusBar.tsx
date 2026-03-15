import './StatusBar.css'

interface StatusBarProps {
  gpsLocked: boolean
  routeReady: boolean
  coachActive: boolean
  weatherLive: boolean
  cityLabel: string
}

function Dot({ color, on }: { color: string; on: boolean }) {
  return <div className="sb-dot" style={{ background: color, opacity: on ? 1 : 0.3 }} />
}

export default function StatusBar({
  gpsLocked,
  routeReady,
  coachActive,
  weatherLive,
  cityLabel,
}: StatusBarProps) {
  return (
    <div className="sb-root">
      <div className="sb-left">
        <div className="sb-item"><Dot color="#38bdf8" on={gpsLocked} />GPS LOCKED</div>
        <div className="sb-item"><Dot color="#10b981" on={routeReady} />ROUTE READY</div>
        <div className="sb-item"><Dot color="#8b5cf6" on={coachActive} />COACH ACTIVE</div>
        <div className="sb-item"><Dot color="#f59e0b" on={weatherLive} />WEATHER LIVE</div>
      </div>
      <div className="sb-item sb-sys">{`SYS · STRIDER v0.1 · ${cityLabel}`}</div>
    </div>
  )
}

