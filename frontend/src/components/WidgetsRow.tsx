import type { Coordinates } from '../types'
import type { WeatherPoint } from '../types/dashboard'

interface WidgetsRowProps {
  weatherLoading: boolean
  weather: WeatherPoint[]
  locationName: string
  currentLocation: Coordinates
  clock: Date
}

export default function WidgetsRow({
  weatherLoading,
  weather,
  locationName,
  currentLocation,
  clock,
}: WidgetsRowProps) {
  return (
    <div className="widgets-row">
      <div className="weather-widget">
        <div className="section-label">WEATHER</div>
        <div className="weather-strip">
          {weatherLoading
            ? Array.from({ length: 8 }).map((_, index) => (
                <div key={index} className="weather-cell weather-loading">
                  <span>--:--</span>
                  <span>--°</span>
                </div>
              ))
            : weather.map((item) => (
                <div key={`${item.hour}-${item.temp}`} className="weather-cell">
                  <span className="weather-time">{item.hour}</span>
                  <span className="weather-temp">{item.temp}</span>
                  <span className={`wx-icon ${item.icon}`} />
                </div>
              ))}
        </div>
      </div>

      <div className="location-widget">
        <div className="section-label">LOCATION</div>
        <div className="location-name">{locationName}</div>
        <div className="coord-readout">{`${currentLocation.lat.toFixed(4)}, ${currentLocation.lng.toFixed(4)}`}</div>
        <div className="clock-readout">
          {clock.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
        </div>
      </div>
    </div>
  )
}

