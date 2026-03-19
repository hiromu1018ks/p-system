import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet'
import L from 'leaflet'

const GSI_TILE_URL = 'https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png'
const GSI_ATTRIBUTION = '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>'

const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})
L.Marker.prototype.options.icon = defaultIcon

function MapCenterUpdater({ center }) {
  const map = useMap()
  const prevCenterRef = useRef(null)

  useEffect(() => {
    if (center && center[0] !== null && center[1] !== null) {
      const key = `${center[0]},${center[1]}`
      if (prevCenterRef.current !== key) {
        map.setView(center, 16)
        prevCenterRef.current = key
      }
    }
  }, [center, map])

  return null
}

export default function PropertyMap({ latitude, longitude, onMapClick, editable = false }) {
  const defaultCenter = [35.6812, 139.7671]
  const hasPosition = latitude != null && longitude != null
  const markerPosition = hasPosition ? [latitude, longitude] : null

  return (
    <div style={{ height: 300, borderRadius: 4, border: '1px solid #ccc' }}>
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
        crossOrigin=""
      />
      <MapContainer
        center={markerPosition || defaultCenter}
        zoom={hasPosition ? 16 : 13}
        style={{ height: '100%', width: '100%' }}
        {...(editable ? { onClick: (e) => onMapClick && onMapClick(e.latlng.lat, e.latlng.lng) } : {})}
      >
        <TileLayer url={GSI_TILE_URL} attribution={GSI_ATTRIBUTION} />
        {markerPosition && <Marker position={markerPosition} />}
        {markerPosition && <MapCenterUpdater center={markerPosition} />}
      </MapContainer>
    </div>
  )
}
