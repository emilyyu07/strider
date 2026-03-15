import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'

import type { Coordinates, RouteResponse } from '../types'

interface MapProps {
  currentLocation: Coordinates | null
  route: RouteResponse | null
}

export default function Map({ currentLocation, route }: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const routeStartMarker = useRef<maplibregl.Marker | null>(null)
  const currentLocationMarker = useRef<maplibregl.Marker | null>(null)

  useEffect(() => {
    if (!mapContainer.current || map.current) {
      return
    }
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: [
              'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
              'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
          },
        },
        layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
      },
      center: [-80.2482, 43.5448],
      zoom: 13,
    })
    map.current.addControl(new maplibregl.NavigationControl(), 'top-right')
    map.current.on('load', () => setMapLoaded(true))

    return () => {
      map.current?.remove()
      map.current = null
    }
  }, [])

  useEffect(() => {
    if (!map.current || !mapLoaded) {
      return
    }

    const lineId = 'route-line'
    const sourceId = 'route-source'
    if (map.current.getLayer(lineId)) {
      map.current.removeLayer(lineId)
    }
    if (map.current.getSource(sourceId)) {
      map.current.removeSource(sourceId)
    }
    routeStartMarker.current?.remove()
    routeStartMarker.current = null
    currentLocationMarker.current?.remove()
    currentLocationMarker.current = null

    if (route && route.route.length > 0) {
      const lineCoordinates = route.route.map(([lat, lng]) => [lng, lat])
      map.current.addSource(sourceId, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: { type: 'LineString', coordinates: lineCoordinates },
          properties: {},
        },
      })
      map.current.addLayer({
        id: lineId,
        type: 'line',
        source: sourceId,
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#2563eb', 'line-width': 4 },
      })

      const [startLat, startLng] = route.route[0]
      routeStartMarker.current = new maplibregl.Marker({ color: '#dc2626' })
        .setLngLat([startLng, startLat])
        .setPopup(new maplibregl.Popup().setText('Route start'))
        .addTo(map.current)

      const bounds = lineCoordinates.reduce(
        (nextBounds, point) => nextBounds.extend(point as [number, number]),
        new maplibregl.LngLatBounds(
          lineCoordinates[0] as [number, number],
          lineCoordinates[0] as [number, number],
        ),
      )
      map.current.fitBounds(bounds, { padding: 50 })
    }

    if (currentLocation) {
      currentLocationMarker.current = new maplibregl.Marker({ color: '#059669' })
        .setLngLat([currentLocation.lng, currentLocation.lat])
        .setPopup(new maplibregl.Popup().setText('Current location'))
        .addTo(map.current)
      if (!route) {
        map.current.flyTo({ center: [currentLocation.lng, currentLocation.lat], zoom: 14 })
      }
    }
  }, [currentLocation, route, mapLoaded])

  return <div ref={mapContainer} className="map-container" />
}
