import { useEffect, useMemo, useRef, useState } from 'react'
import axios from 'axios'

import type { Coordinates, LLMRouteParameters, RouteResponse } from '../../types'
import { generateRoute, regenerateRoute } from '../../services/api'
import CoachPanel from './CoachPanel'
import MapPanel from './MapPanel'
import RoutePanel from './RoutePanel'
import StatusBar from './StatusBar'
import TopNav from './TopNav'
import WeatherStrip, { type RunWindowSegment } from './WeatherStrip'
import './Dashboard.css'

const TERRAIN_TAGS = ['QUIET', 'SHADED', 'HILLY', 'FLAT', 'LOW TRAFFIC', 'PARK', 'WATERFRONT', 'SCENIC']
const FALLBACK_LOCATION: Coordinates = { lat: 43.4643, lng: -80.5204 }

interface WeatherState {
  tempC: number
  feelsLikeC: number
  condition: string
  windKmh: number
  windDirectionDeg: number
  precip1h: number
  humidity: number
  uvIndex: number
  sunrise: string
  sunset: string
  goldenHour: string
  hourlyTemp: number[]
  hourlyPrecip: number[]
  hourlyWind: number[]
}

const DEFAULT_WEATHER: WeatherState = {
  tempC: 12,
  feelsLikeC: 8,
  condition: 'Partly clear',
  windKmh: 14,
  windDirectionDeg: 315,
  precip1h: 14,
  humidity: 61,
  uvIndex: 3,
  sunrise: '--:--',
  sunset: '--:--',
  goldenHour: '--:--',
  hourlyTemp: Array(16).fill(12),
  hourlyPrecip: Array(16).fill(14),
  hourlyWind: Array(16).fill(14),
}

function formatClock(date: Date): string {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function formatShortTime(value: string | undefined): string {
  if (!value) return '--:--'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '--:--'
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function windDirectionLabel(deg: number): string {
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  const index = Math.round((((deg % 360) + 360) % 360) / 45) % 8
  return dirs[index]
}

function weatherCodeToText(code: number): string {
  if ([61, 63, 65, 80, 81, 82].includes(code)) return 'Rain'
  if ([1, 2, 3, 45, 48].includes(code)) return 'Partly clear'
  return 'Clear'
}

function buildWeatherCoachBrief({
  locationName,
  weather,
}: {
  locationName: string
  weather: WeatherState
}): string {
  const wind = Math.round(weather.windKmh)
  const precip = Math.round(weather.precip1h)
  const temp = Math.round(weather.tempC)
  if (precip >= 45) {
    return `Rain risk is elevated in ${locationName}. Keep this run controlled, shorten stride, and favor good traction routes.`
  }
  if (wind >= 25) {
    return `Wind is up in ${locationName}. Start conservative into the headwind and finish strong with the tailwind.`
  }
  if (temp >= 24) {
    return `Warm conditions in ${locationName}. Open easy, hydrate early, and keep your effort smooth over pace.`
  }
  return `Conditions look runnable in ${locationName}: ${temp}°C, ${wind} km/h wind. Settle in early and build through the second half.`
}

function normalizeCoachText(value: unknown, fallback: string): string {
  if (typeof value !== 'string' || !value.trim()) {
    return fallback
  }
  const cleaned = value.replace(/^```(?:json)?/i, '').replace(/```$/, '').trim()
  try {
    const parsed = JSON.parse(cleaned) as unknown
    if (typeof parsed === 'string' && parsed.trim()) {
      return parsed.replace(/\s+/g, ' ').trim()
    }
    if (parsed && typeof parsed === 'object') {
      const record = parsed as Record<string, unknown>
      for (const key of ['message', 'coach_message', 'advice', 'text']) {
        const entry = record[key]
        if (typeof entry === 'string' && entry.trim()) {
          return entry.replace(/\s+/g, ' ').trim()
        }
      }
    }
  } catch {
    return cleaned.replace(/\s+/g, ' ').trim()
  }
  return fallback
}

function buildRunWindowSegments(weather: WeatherState): RunWindowSegment[] {
  return Array.from({ length: 16 }).map((_, index) => {
    const temp = weather.hourlyTemp[index] ?? weather.tempC
    const precip = weather.hourlyPrecip[index] ?? weather.precip1h
    const wind = weather.hourlyWind[index] ?? weather.windKmh
    if (precip > 40) return { label: 'rain' }
    let score = 0
    if (temp >= 5 && temp <= 18) score += 1
    if (precip < 20) score += 1
    if (wind < 20) score += 1
    if (score === 3) return { label: 'best' }
    if (score === 2) return { label: 'good' }
    if (score === 1) return { label: 'ok' }
    return { label: 'poor' }
  })
}

function summarizeBestWindow(segments: RunWindowSegment[], now: Date): string {
  let bestStart = -1
  let bestLen = 0
  let i = 0
  while (i < segments.length) {
    if (segments[i]?.label !== 'best') {
      i += 1
      continue
    }
    let j = i
    while (j < segments.length && segments[j]?.label === 'best') {
      j += 1
    }
    if (j - i > bestLen) {
      bestLen = j - i
      bestStart = i
    }
    i = j
  }
  if (bestStart < 0) {
    return 'BEST WINDOW · NONE · CONDITIONS VARIABLE'
  }
  const start = new Date(now.getTime() + bestStart * 30 * 60 * 1000)
  const end = new Date(now.getTime() + (bestStart + bestLen) * 30 * 60 * 1000)
  return `BEST WINDOW · ${formatClock(start)} – ${formatClock(end)} · LOW WIND · CLEAR`
}

export default function Dashboard() {
  const [now, setNow] = useState(new Date())
  const [location, setLocation] = useState<Coordinates>(FALLBACK_LOCATION)
  const [locationName, setLocationName] = useState('WATERLOO, ON')
  const [weather, setWeather] = useState<WeatherState>(DEFAULT_WEATHER)
  const [aqi, setAqi] = useState(22)
  const [weatherLive, setWeatherLive] = useState(false)
  const [gpsLocked, setGpsLocked] = useState(false)
  const [prompt, setPrompt] = useState('')
  const [distanceM, setDistanceM] = useState(5000)
  const [paceIndex, setPaceIndex] = useState(2)
  const [selectedTerrain, setSelectedTerrain] = useState<string[]>(['QUIET', 'LOW TRAFFIC'])
  const [loading, setLoading] = useState(false)
  const [route, setRoute] = useState<RouteResponse | null>(null)
  const [lastParams, setLastParams] = useState<LLMRouteParameters | null>(null)
  const [coachMessage, setCoachMessage] = useState('AWAITING WEATHER BRIEF...')
  const advisoryLoadedRef = useRef(false)

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    if (!navigator.geolocation) {
      return
    }
    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        setLocation({ lat: position.coords.latitude, lng: position.coords.longitude })
        setGpsLocked(true)
      },
      () => setGpsLocked(false),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 1500 },
    )
    return () => navigator.geolocation.clearWatch(watchId)
  }, [])

  useEffect(() => {
    let active = true
    const loadLocation = async () => {
      try {
        const res = await fetch(
          `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${location.lat}&longitude=${location.lng}&localityLanguage=en`,
        )
        const data = (await res.json()) as { city?: string; locality?: string; principalSubdivision?: string }
        if (!active) return
        const city = (data.city || data.locality || 'WATERLOO').toUpperCase()
        const region = (data.principalSubdivision || 'ON').toUpperCase()
        setLocationName(`${city}, ${region}`)
      } catch {
        if (active) setLocationName('WATERLOO, ON')
      }
    }
    void loadLocation()
    return () => {
      active = false
    }
  }, [location.lat, location.lng])

  useEffect(() => {
    let active = true
    const loadWeather = async () => {
      try {
        const weatherUrl =
          `https://api.open-meteo.com/v1/forecast?latitude=${location.lat}&longitude=${location.lng}` +
          '&hourly=temperature_2m,apparent_temperature,precipitation_probability,windspeed_10m,wind_speed_10m,uv_index,relativehumidity_2m,relative_humidity_2m,weathercode' +
          '&daily=sunrise,sunset&current_weather=true&forecast_days=1&timezone=auto'
        const [wxRes, aqiRes] = await Promise.all([
          fetch(weatherUrl),
          fetch(
            `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${location.lat}&longitude=${location.lng}&hourly=us_aqi&timezone=auto&forecast_days=1`,
          ),
        ])
        const wx = (await wxRes.json()) as Record<string, any>
        const air = (await aqiRes.json()) as Record<string, any>
        if (!active) return

        const hourly = (wx.hourly ?? {}) as Record<string, any[]>
        const nowHour = new Date().getHours()
        const from = nowHour
        const to16 = (arr: any[] | undefined, fallback: number) =>
          Array.from({ length: 16 }).map((_, i) => Number(arr?.[from + Math.floor(i / 2)] ?? fallback))

        const humidityValues = hourly.relative_humidity_2m ?? hourly.relativehumidity_2m ?? []
        const windValues = hourly.wind_speed_10m ?? hourly.windspeed_10m ?? []
        const precipValues = hourly.precipitation_probability ?? []
        const tempValues = hourly.temperature_2m ?? []
        const apparentValues = hourly.apparent_temperature ?? tempValues
        const uvValues = hourly.uv_index ?? []
        const codeValues = hourly.weathercode ?? []
        const currentTemp = Number(wx.current_weather?.temperature ?? tempValues[from] ?? 12)
        const currentWind = Number(wx.current_weather?.windspeed ?? windValues[from] ?? 14)
        const currentWindDir = Number(wx.current_weather?.winddirection ?? 315)
        const currentPrecip = Number(precipValues[from] ?? 14)
        const currentHumidity = Number(humidityValues[from] ?? 61)
        const currentUv = Number(uvValues[from] ?? 3)
        const currentFeels = Number(apparentValues[from] ?? currentTemp - 2)
        const weatherCode = Number(wx.current_weather?.weathercode ?? codeValues[from] ?? 1)
        const sunrise = formatShortTime(wx.daily?.sunrise?.[0])
        const sunset = formatShortTime(wx.daily?.sunset?.[0])
        const sunsetDate = wx.daily?.sunset?.[0] ? new Date(wx.daily.sunset[0]) : new Date()
        sunsetDate.setMinutes(sunsetDate.getMinutes() - 30)

        setWeather({
          tempC: currentTemp,
          feelsLikeC: currentFeels,
          condition: weatherCodeToText(weatherCode),
          windKmh: currentWind,
          windDirectionDeg: currentWindDir,
          precip1h: currentPrecip,
          humidity: currentHumidity,
          uvIndex: currentUv,
          sunrise,
          sunset,
          goldenHour: formatClock(sunsetDate),
          hourlyTemp: to16(tempValues, currentTemp),
          hourlyPrecip: to16(precipValues, currentPrecip),
          hourlyWind: to16(windValues, currentWind),
        })
        const airHourly = (air.hourly?.us_aqi as number[]) ?? []
        setAqi(Math.round(Number(airHourly[from] ?? 22)))
        setWeatherLive(true)
      } catch {
        if (active) setWeatherLive(false)
      }
    }
    void loadWeather()
    return () => {
      active = false
    }
  }, [location.lat, location.lng])

  useEffect(() => {
    if (!weatherLive || advisoryLoadedRef.current || route) return
    advisoryLoadedRef.current = true
    setCoachMessage(buildWeatherCoachBrief({ locationName, weather }))
  }, [locationName, route, weather, weatherLive])

  const runSegments = useMemo(() => buildRunWindowSegments(weather), [weather])
  const bestWindowSummary = useMemo(() => summarizeBestWindow(runSegments, now), [now, runSegments])
  const nowLinePercent = useMemo(() => (now.getMinutes() / 60 / 8) * 100, [now])
  const timeLabels = useMemo(
    () =>
      Array.from({ length: 9 }).map((_, index) =>
        index === 0 ? 'NOW' : formatClock(new Date(now.getTime() + index * 60 * 60 * 1000)),
      ),
    [now],
  )

  const handleToggleTerrain = (tag: string) => {
    setSelectedTerrain((prev) => (prev.includes(tag) ? prev.filter((p) => p !== tag) : [...prev, tag]))
  }

  const handleGenerateRoute = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    try {
      const response = await generateRoute({
        prompt: prompt.trim(),
        distance_m: distanceM,
        preferences: selectedTerrain.map((s) => s.toLowerCase().replaceAll(' ', '_')),
        current_location: location,
      })
      setRoute(response)
      setLastParams(response.parameters)
      setCoachMessage(normalizeCoachText(response.coach_message, 'Route generated. Stay smooth and controlled.'))
    } catch (error) {
      if (axios.isAxiosError(error)) {
        setCoachMessage(error.response?.data?.detail ?? 'Route generation failed.')
      } else {
        setCoachMessage('Route generation failed.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRegenerateRoute = async () => {
      if (!lastParams || loading) return
    setLoading(true)
    try {
      const response = await regenerateRoute({
        previous_parameters: lastParams,
        current_location: location,
      })
      setRoute(response)
      setLastParams(response.parameters)
      setCoachMessage(normalizeCoachText(response.coach_message, 'Route regenerated. Keep your cadence steady.'))
    } catch {
      setCoachMessage('Regeneration failed. Keep current route and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="shell">
      <TopNav
        locationName={locationName}
        tempC={weather.tempC}
        feelsLikeC={weather.feelsLikeC}
        windKmh={weather.windKmh}
        windDir={windDirectionLabel(weather.windDirectionDeg)}
        precip1h={weather.precip1h}
        clock={formatClock(now)}
      />

      <WeatherStrip
        tempC={weather.tempC}
        condition={weather.condition}
        feelsLikeC={weather.feelsLikeC}
        windKmh={weather.windKmh}
        windDir={windDirectionLabel(weather.windDirectionDeg)}
        humidity={weather.humidity}
        uvIndex={weather.uvIndex}
        aqi={aqi}
        sunrise={weather.sunrise}
        sunset={weather.sunset}
        goldenHour={weather.goldenHour}
        precip1h={weather.precip1h}
        runSegments={runSegments}
        nowLinePercent={nowLinePercent}
        timeLabels={timeLabels}
        bestWindowSummary={bestWindowSummary}
      />

      <div className="body">
        <RoutePanel
          prompt={prompt}
          distanceM={distanceM}
          terrainTags={TERRAIN_TAGS}
          selectedTerrain={selectedTerrain}
          paceIndex={paceIndex}
          loading={loading}
          hasRoute={Boolean(route)}
          onPromptChange={setPrompt}
          onDistanceChange={setDistanceM}
          onPaceChange={setPaceIndex}
          onToggleTerrain={handleToggleTerrain}
          onClearTerrain={() => setSelectedTerrain([])}
          onGenerate={handleGenerateRoute}
          onRegenerate={handleRegenerateRoute}
        />
        <div className="right">
          <MapPanel locationName={locationName} currentLocation={location} route={route} />
          <CoachPanel message={coachMessage} />
          <StatusBar
            gpsLocked={gpsLocked}
            routeReady={Boolean(route)}
            coachActive={Boolean(coachMessage)}
            weatherLive={weatherLive}
            cityLabel={locationName.split(',')[0]}
          />
        </div>
      </div>
    </div>
  )
}

