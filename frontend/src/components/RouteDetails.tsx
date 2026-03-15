import type { RouteResponse } from '../types'

interface RouteDetailsProps {
  route: RouteResponse | null
}

export default function RouteDetails({ route }: RouteDetailsProps) {
  if (!route) {
    return <p>No route generated yet.</p>
  }

  const distanceKm = (route.distance_m / 1000).toFixed(2)
  const durationMin = Math.round(route.duration_estimate_s / 60)
  return (
    <div>
      <h3>Route details</h3>
      <p>Distance: {distanceKm} km</p>
      <p>Estimated duration: {durationMin} min</p>
      <p>{route.description}</p>
      {route.parameters.preferences.length > 0 && (
        <p>Preferences: {route.parameters.preferences.join(', ')}</p>
      )}
    </div>
  )
}
