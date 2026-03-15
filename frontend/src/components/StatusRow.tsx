interface StatusRowProps {
  gpsLocked: boolean
  routeReady: boolean
  coachActive: boolean
}

export default function StatusRow({ gpsLocked, routeReady, coachActive }: StatusRowProps) {
  return (
    <div className="status-row">
      <div className="status-items">
        <span className="status-item">
          <span className={`tiny-dot ${gpsLocked ? 'dot-on' : ''}`} />
          GPS LOCKED
        </span>
        <span className="status-item">
          <span className={`tiny-dot green ${routeReady ? 'dot-on' : ''}`} />
          ROUTE READY
        </span>
        <span className="status-item">
          <span className={`tiny-dot purple ${coachActive ? 'dot-on' : ''}`} />
          COACH ACTIVE
        </span>
      </div>
      <div className="sys-label">SYS · STRIDER v0.1</div>
    </div>
  )
}

