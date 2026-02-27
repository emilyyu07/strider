/**
* Route details panel
*/

import type { GeoJSONResponse } from '../types';

interface RouteDetailsProps {
route: GeoJSONResponse | null;
}

export default function RouteDetails({ route }: RouteDetailsProps) {
if (!route || route.features.length === 0) {
return (
<div className="text-center text-gray-500 py-8">
<svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
</svg>
<p className="mt-2 text-sm">No route generated yet</p>
<p className="text-xs text-gray-400 mt-1">
Click on the map to set start and end points
</p>
</div>
);
}

const props = route.features[0].properties;

return (
<div className="space-y-4">
{/* Distance */}
<div className="bg-primary/10 rounded-lg p-4">
<div className="text-center">
<div className="text-3xl font-bold text-primary">
{props.distance_km} km
</div>
<div className="text-sm text-gray-600">
{props.segment_count} segments
</div>
</div>
</div>

{/* Stats */}
<div className="grid grid-cols-2 gap-3">
<div className="bg-gray-50 rounded-lg p-3">
<div className="text-xs text-gray-500">Lit Streets</div>
<div className="text-lg font-semibold">
{props.lit_segments}/{props.segment_count}
</div>
</div>
<div className="bg-gray-50 rounded-lg p-3">
<div className="text-xs text-gray-500">Scenic</div>
<div className="text-lg font-semibold">
{props.scenic_segments}/{props.segment_count}
</div>
</div>
</div>

{/* LLM Reasoning */}
{props.llm_reasoning && (
<div className="border-t pt-4">
<div className="text-sm font-medium text-gray-700 mb-2">
AI Analysis
</div>
<div className="text-xs text-gray-600 bg-gray-50 rounded p-3">
{props.llm_reasoning}
</div>
</div>
)}

{/* Preferences */}
{props.llm_preferences && Object.keys(props.llm_preferences).length > 0 && (
<div className="border-t pt-4">
<div className="text-sm font-medium text-gray-700 mb-2">
Routing Preferences
</div>
<div className="space-y-1">
{Object.entries(props.llm_preferences).map(([key, value]) => (
<div key={key} className="flex justify-between text-xs">
<span className="text-gray-600 capitalize">{key}</span>
<span className={`font-mono ${
value > 1 ? 'text-red-600' : 'text-green-600'
}`}>
{value > 1 ? 'Avoid' : 'Prefer'} (×{value.toFixed(1)})
</span>
</div>
))}
</div>
</div>
)}

{/* Performance */}
{props.performance && (
<div className="border-t pt-4">
<div className="text-sm font-medium text-gray-700 mb-2">
Performance
</div>
<div className="text-xs text-gray-600 space-y-1">
<div className="flex justify-between">
<span>Total Time:</span>
<span className="font-mono">{props.performance.total_time_s.toFixed(2)}s</span>
</div>
<div className="flex justify-between">
<span>LLM Analysis:</span>
<span className="font-mono">{props.performance.llm_time_s.toFixed(2)}s</span>
</div>
<div className="flex justify-between">
<span>Route Calc:</span>
<span className="font-mono">{props.performance.routing_time_s.toFixed(2)}s</span>
</div>
</div>
</div>
)}
</div>
);
}