import './TopNav.css'

interface TopNavProps {
  locationName: string
  tempC: number
  feelsLikeC: number
  windKmh: number
  windDir: string
  precip1h: number
  clock: string
}

export default function TopNav({
  locationName,
  tempC,
  feelsLikeC,
  windKmh,
  windDir,
  precip1h,
  clock,
}: TopNavProps) {
  return (
    <div className="topbar">
      <div className="nav-left">
        <span className="nav-logo">STRIDER</span>
        <div className="nav-dot" />
      </div>

      <div className="nav-links">
        <span className="nav-link active">MAP</span>
        <span className="nav-link">HISTORY</span>
      </div>

      <div className="nav-right">
        <div className="nav-weather-quick">
          <div className="nwq-item">
            <span className="nwq-label">LOCATION</span>
            <span className="nwq-val bright">{locationName}</span>
          </div>
          <div className="nwq-divider" />
          <div className="nwq-item">
            <span className="nwq-label">TEMP · FEELS</span>
            <span className="nwq-val">{`${Math.round(tempC)}°C · FEELS ${Math.round(feelsLikeC)}°C`}</span>
          </div>
          <div className="nwq-divider" />
          <div className="nwq-item">
            <span className="nwq-label">WIND</span>
            <span className="nwq-val">
              <span className="wind-arrow">↑</span>
              {`${Math.round(windKmh)} KM/H · ${windDir}`}
            </span>
          </div>
          <div className="nwq-divider" />
          <div className="nwq-item">
            <span className="nwq-label">PRECIP · 1H</span>
            <span className="nwq-val good">{`${Math.round(precip1h)}%`}</span>
          </div>
          <div className="nwq-divider" />
          <span className="clock">{clock}</span>
        </div>
      </div>
    </div>
  )
}

