import './WeatherStrip.css'

export type RunWindowClass = 'best' | 'good' | 'ok' | 'rain' | 'poor'

export interface RunWindowSegment {
  label: RunWindowClass
}

interface WeatherStripProps {
  tempC: number
  condition: string
  feelsLikeC: number
  windKmh: number
  windDir: string
  humidity: number
  uvIndex: number
  aqi: number
  sunrise: string
  sunset: string
  goldenHour: string
  precip1h: number
  runSegments: RunWindowSegment[]
  nowLinePercent: number
  timeLabels: string[]
  bestWindowSummary: string
}

function humidityLabel(value: number): string {
  if (value < 35) return 'DRY'
  if (value <= 70) return 'MODERATE'
  return 'HUMID'
}

function aqiLabel(aqi: number): string {
  if (aqi <= 50) return 'GOOD'
  if (aqi <= 100) return 'MODERATE'
  return 'POOR'
}

export default function WeatherStrip({
  tempC,
  condition,
  feelsLikeC,
  windKmh,
  windDir,
  humidity,
  uvIndex,
  aqi,
  sunrise,
  sunset,
  goldenHour,
  precip1h,
  runSegments,
  nowLinePercent,
  timeLabels,
  bestWindowSummary,
}: WeatherStripProps) {
  const uvSegmentsFilled = Math.min(8, Math.max(0, Math.round((uvIndex / 11) * 8)))

  return (
    <div className="wx-strip">
      <div className="wx-main-row">
        <div className="wx-temp-block">
          <span className="wx-temp-big">{`${Math.round(tempC)}°`}</span>
          <span className="wx-condition">{condition.toUpperCase()}</span>
          <span className="wx-feels">
            FEELS LIKE <span>{`${Math.round(feelsLikeC)}°C`}</span>
          </span>
        </div>

        <div className="wx-stats">
          <div className="wx-stat">
            <span className="wx-stat-label">WIND</span>
            <span className="wx-stat-val">
              <span className="wind-arrow">↑</span>
              {`${Math.round(windKmh)} KM/H`}
            </span>
            <span className="wx-stat-sub">{`FROM ${windDir}`}</span>
          </div>
          <div className="wx-stat">
            <span className="wx-stat-label">HUMIDITY</span>
            <span className="wx-stat-val">{`${Math.round(humidity)}%`}</span>
            <span className="wx-stat-sub">{humidityLabel(humidity)}</span>
          </div>
          <div className="wx-stat">
            <span className="wx-stat-label">UV INDEX</span>
            <span className="wx-stat-val">{`${Math.round(uvIndex)} · ${uvIndex <= 2 ? 'LOW' : uvIndex <= 5 ? 'MOD' : 'HIGH'}`}</span>
            <div className="uv-bar">
              {Array.from({ length: 8 }).map((_, i) => {
                const segClass = i < uvSegmentsFilled ? (i < 3 ? 'low' : i < 5 ? 'mid' : 'high') : ''
                return <div key={i} className={`uv-seg ${segClass}`.trim()} />
              })}
            </div>
          </div>
          <div className="wx-stat">
            <span className="wx-stat-label">AIR QUALITY</span>
            <span className="wx-stat-val aqi-value">{`AQI ${Math.round(aqi)}`}</span>
            <div className="aqi-pill">
              <div className="aqi-dot" />
              <span className="aqi-text">{aqiLabel(aqi)}</span>
            </div>
          </div>
          <div className="wx-stat">
            <span className="wx-stat-label">SUNRISE · SET</span>
            <div className="sun-row">
              <div className="sun-icon" />
              <span className="wx-stat-val sun-time">{sunrise}</span>
            </div>
            <span className="wx-stat-sub">
              {`SETS ${sunset} · `}
              <span className="golden">{`GOLDEN ${goldenHour}`}</span>
            </span>
          </div>
          <div className="wx-stat">
            <span className="wx-stat-label">PRECIP · 1H</span>
            <span className="wx-stat-val precip-value">{`${Math.round(precip1h)}%`}</span>
            <div className="precip-track">
              <div className="precip-fill" style={{ width: `${Math.max(0, Math.min(100, precip1h))}%` }} />
            </div>
          </div>
        </div>
      </div>

      <div className="run-window">
        <div className="rw-header">
          <span className="rw-label">RUN WINDOW · NEXT 8 HOURS</span>
          <span className="rw-best">{bestWindowSummary}</span>
        </div>
        <div className="rw-track">
          <div className="rw-segments">
            {runSegments.map((segment, index) => (
              <div key={index} className={`rw-seg ${segment.label}`}>
                <div className="rw-seg-fill" />
              </div>
            ))}
          </div>
          <div className="rw-now-line" style={{ left: `${nowLinePercent}%` }} />
        </div>
        <div className="rw-times">
          {timeLabels.map((label, index) => (
            <span key={`${label}-${index}`} className={`rw-time ${index === 0 ? 'now-t' : ''}`}>
              {label}
            </span>
          ))}
        </div>
        <div className="rw-footer">
          <div className="rw-legend">
            <div className="rw-leg"><div className="rw-leg-dot best-dot" />OPTIMAL</div>
            <div className="rw-leg"><div className="rw-leg-dot good-dot" />GOOD</div>
            <div className="rw-leg"><div className="rw-leg-dot ok-dot" />OKAY</div>
            <div className="rw-leg"><div className="rw-leg-dot rain-dot" />RAIN</div>
            <div className="rw-leg"><div className="rw-leg-dot poor-dot" />POOR</div>
          </div>
          <div className="best-window">{bestWindowSummary}</div>
        </div>
      </div>
    </div>
  )
}

