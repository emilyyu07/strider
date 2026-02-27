/**
* MapLibre GL map component
*/

import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import type { Coordinates, GeoJSONResponse } from '../types';

interface MapProps {
onMapClick: (coords: Coordinates) => void;
startPoint: Coordinates | null;
endPoint: Coordinates | null;
route: GeoJSONResponse | null;
}

export default function Map({ onMapClick, startPoint, endPoint, route }: MapProps) {
const mapContainer = useRef<HTMLDivElement>(null);
const map = useRef<maplibregl.Map | null>(null);
const [mapLoaded, setMapLoaded] = useState(false);

// Markers
const startMarker = useRef<maplibregl.Marker | null>(null);
const endMarker = useRef<maplibregl.Marker | null>(null);

// Initialize map
useEffect(() => {
if (!mapContainer.current) return;
if (map.current) return; // Initialize only once

// Create map
map.current = new maplibregl.Map({
container: mapContainer.current,
style: {
version: 8,
sources: {
'osm': {
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
layers: [
{
id: 'osm',
type: 'raster',
source: 'osm',
minzoom: 0,
maxzoom: 19,
},
],
},
center: [-80.248, 43.544], // Guelph, ON
zoom: 13,
});

// Add navigation controls
map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

// Add scale
map.current.addControl(new maplibregl.ScaleControl(), 'bottom-left');

// Handle map click
map.current.on('click', (e) => {
onMapClick({ lng: e.lngLat.lng, lat: e.lngLat.lat });
});

// Map loaded
map.current.on('load', () => {
setMapLoaded(true);
});

// Cleanup
return () => {
map.current?.remove();
map.current = null;
};
}, [onMapClick]);

// Update start marker
useEffect(() => {
if (!map.current || !mapLoaded) return;

// Remove old marker
if (startMarker.current) {
startMarker.current.remove();
}

// Add new marker
if (startPoint) {
startMarker.current = new maplibregl.Marker({ color: '#ef4444' }) // Red
.setLngLat([startPoint.lng, startPoint.lat])
.setPopup(new maplibregl.Popup().setHTML('<strong>Start</strong>'))
.addTo(map.current);
}
}, [startPoint, mapLoaded]);

// Update end marker
useEffect(() => {
if (!map.current || !mapLoaded) return;

// Remove old marker
if (endMarker.current) {
endMarker.current.remove();
}

// Add new marker
if (endPoint) {
endMarker.current = new maplibregl.Marker({ color: '#3b82f6' }) // Blue
.setLngLat([endPoint.lng, endPoint.lat])
.setPopup(new maplibregl.Popup().setHTML('<strong>End</strong>'))
.addTo(map.current);
}
}, [endPoint, mapLoaded]);

// Update route
useEffect(() => {
if (!map.current || !mapLoaded) return;

// Remove old route layer
if (map.current.getLayer('route')) {
map.current.removeLayer('route');
}
if (map.current.getSource('route')) {
map.current.removeSource('route');
}

// Add new route
if (route && route.features.length > 0) {
map.current.addSource('route', {
type: 'geojson',
data: route as any,
});

map.current.addLayer({
id: 'route',
type: 'line',
source: 'route',
layout: {
'line-join': 'round',
'line-cap': 'round',
},
paint: {
'line-color': '#3b82f6',
'line-width': 4,
'line-opacity': 0.8,
},
});

// Fit map to route bounds
const coordinates = route.features[0].geometry.coordinates as number[][];
const bounds = coordinates.reduce(
(bounds, coord) => bounds.extend(coord as [number, number]),
new maplibregl.LngLatBounds(coordinates[0] as [number, number], coordinates[0] as [number, number])
);

map.current.fitBounds(bounds, { padding: 50 });
}
}, [route, mapLoaded]);

return (
<div className="relative w-full h-full">
<div ref={mapContainer} className="absolute inset-0" />
</div>
);
}