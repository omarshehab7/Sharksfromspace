# API Reference

Base URL: `http://localhost:8000/api/v1`

## Health

### `GET /health`

Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "sharks-from-space-api",
  "version": "1.0.0"
}
```

---

## Hotspots

### `GET /hotspots`

Retrieve predicted shark activity hotspots.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `min_lat` | float | No | Minimum latitude (-90 to 90) |
| `max_lat` | float | No | Maximum latitude (-90 to 90) |
| `min_lon` | float | No | Minimum longitude (-180 to 180) |
| `max_lon` | float | No | Maximum longitude (-180 to 180) |
| `risk_level` | string | No | Filter: `low`, `medium`, or `high` |
| `limit` | int | No | Max results (1-200, default: 50) |

**Response:**
```json
{
  "hotspots": [
    {
      "id": "h-001",
      "latitude": 25.76,
      "longitude": -80.19,
      "risk_score": 0.85,
      "risk_level": "high",
      "sst": 27.3,
      "sst_anomaly": 1.2,
      "chlorophyll": 0.45,
      "depth": 85.0,
      "current_speed": 0.32,
      "species": ["Tiger Shark", "Bull Shark"],
      "predicted_at": "2024-01-15T12:00:00Z"
    }
  ],
  "total": 1,
  "last_updated": "2024-01-15T12:00:00Z"
}
```

### `GET /hotspots/{hotspot_id}`

Get detailed information for a specific hotspot.

**Response:** Same as single hotspot object above.

---

## Ocean Data

### `GET /ocean-data`

Get ocean parameters for a specific location.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `lat` | float | Yes | Latitude (-90 to 90) |
| `lon` | float | Yes | Longitude (-180 to 180) |

**Response:**
```json
{
  "latitude": 25.76,
  "longitude": -80.19,
  "sst": 27.3,
  "chlorophyll": 0.45,
  "depth": 85.0,
  "current_speed": 0.32,
  "current_direction": 180.0,
  "salinity": 35.2,
  "timestamp": "2024-01-15T12:00:00Z"
}
```
