export function toMapLibreLineCoordinates(routePolyline: [number, number][]): [number, number][] {
  return routePolyline.map(([lat, lng]) => [lng, lat])
}

