/**
* Sidebar component
*/

import type { Coordinates, GeoJSONResponse } from '../types';
import PromptInput from './PromptInput';
import RouteDetails from './RouteDetails';

interface SidebarProps {
startPoint: Coordinates | null;
endPoint: Coordinates | null;
route: GeoJSONResponse | null;
loading: boolean;
error: string | null;
onPromptSubmit: (prompt: string) => void;
onReset: () => void;
}

export default function Sidebar({
startPoint,
endPoint,
route,
loading,
error,
onPromptSubmit,
onReset,
}: SidebarProps) {
const hasPoints = startPoint && endPoint;

return (
<div className="w-96 h-full bg-white shadow-lg flex flex-col">
{/* Header */}
<div className="p-6 border-b">
<h1 className="text-2xl font-bold text-gray-800">Strider</h1>
<p className="text-sm text-gray-500 mt-1">
AI-powered route planning
</p>
</div>

{/* Content */}
<div className="flex-1 overflow-y-auto p-6 space-y-6">
{/* Instructions */}
{!startPoint && (
<div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
<div className="flex">
<div className="flex-shrink-0">
<svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
<path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
</svg>
</div>
<div className="ml-3">
<h3 className="text-sm font-medium text-blue-800">
Get Started
</h3>
<div className="mt-2 text-sm text-blue-700">
<ol className="list-decimal list-inside space-y-1">
<li>Click on the map to set your start point</li>
<li>Click again to set your end point</li>
<li>Describe your ideal run</li>
<li>Click "Plan Route"</li>
</ol>
</div>
</div>
</div>
</div>
)}

{/* Points Status */}
{startPoint && (
<div className="space-y-2">
<div className="flex items-center text-sm">
<div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div>
<span className="text-gray-700">
Start: {startPoint.lat.toFixed(4)}, {startPoint.lng.toFixed(4)}
</span>
</div>
{endPoint && (
<div className="flex items-center text-sm">
<div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
<span className="text-gray-700">
End: {endPoint.lat.toFixed(4)}, {endPoint.lng.toFixed(4)}
</span>
</div>
)}
</div>
)}

{/* Error */}
{error && (
<div className="bg-red-50 border border-red-200 rounded-lg p-4">
<div className="flex">
<div className="flex-shrink-0">
<svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
<path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
</svg>
</div>
<div className="ml-3">
<h3 className="text-sm font-medium text-red-800">Error</h3>
<div className="mt-2 text-sm text-red-700">{error}</div>
</div>
</div>
</div>
)}

{/* Prompt Input */}
<PromptInput
onSubmit={onPromptSubmit}
loading={loading}
disabled={!hasPoints}
/>

{/* Route Details */}
<RouteDetails route={route} />
</div>

{/* Footer */}
<div className="p-6 border-t">
<button
onClick={onReset}
className="w-full py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
>
Reset Map
</button>
</div>
</div>
);
}