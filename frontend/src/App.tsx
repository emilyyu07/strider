/**
* Main Strider application
*/

import { useState } from 'react';
import Map from './components/Map';
import Sidebar from './components/Sidebar';
import type { Coordinates, GeoJSONResponse } from './types';
import { planRoute } from './services/api';
import axios from 'axios';

export default function App() {
const [startPoint, setStartPoint] = useState<Coordinates | null>(null);
const [endPoint, setEndPoint] = useState<Coordinates | null>(null);
const [route, setRoute] = useState<GeoJSONResponse | null>(null);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

// Handle map click
const handleMapClick = (coords: Coordinates) => {
  if (!startPoint) {
    setStartPoint(coords);
    setEndPoint(null);
    setRoute(null);
  } else if (!endPoint) {
    setEndPoint(coords);
  } else {
  // Reset and set new start point
    setStartPoint(coords);
    setEndPoint(null);
    setRoute(null);
  }
  setError(null);
};

// Handle prompt submit
const handlePromptSubmit = async (prompt: string) => {
if (!startPoint || !endPoint) {
  setError('Please set both start and end points on the map');
  return;
}

setLoading(true);
setError(null);

try {
  const response = await planRoute({
  prompt,
  start_lon: startPoint.lng,
  start_lat: startPoint.lat,
  end_lon: endPoint.lng,
  end_lat: endPoint.lat,
  });

setRoute(response);
} catch (err: unknown) {
if (axios.isAxiosError(err)) {
    console.error('API Error:', err.response?.data || err.message);
    setError(err.response?.data?.detail || 'Failed to fetch route');
  } else if (err instanceof Error) {
    console.error('Standard Error:', err.message);
    setError(err.message);
  } else {
    console.error('Unknown Error:', err);
    setError('An unexpected error occurred');
  }

} finally {
setLoading(false);
}
};

// Handle reset
const handleReset = () => {
setStartPoint(null);
setEndPoint(null);
setRoute(null);
setError(null);
};

return (
<div className="flex h-screen">
<Sidebar
startPoint={startPoint}
endPoint={endPoint}
route={route}
loading={loading}
error={error}
onPromptSubmit={handlePromptSubmit}
onReset={handleReset}
/>
<div className="flex-1">
<Map
onMapClick={handleMapClick}
startPoint={startPoint}
endPoint={endPoint}
route={route}
/>
</div>
</div>
);
}