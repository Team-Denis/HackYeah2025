# HackYeah2025 API

This API provides a real-time incident reporting system with GTFS-Realtime integration and Redis/SQLite storage. It allows submitting reports, fetching incidents, and generating real-time trip updates.

---

## Configuration

1. Copy `.env.example` to `.env` and adjust variables:

```
HOST=0.0.0.0
PORT=5000
DB_PATH=db/app.db
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
ENQUEUE_URL=http://localhost:5000/enqueue
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Run the Flask server:

```
python web/app.py
```

---

## Endpoints



### 1. `/gtfs/trip-updates` [GET]

Generates a GTFS-Realtime feed for recent incidents.  
This feed can be consumed by GTFS-compatible clients for real-time trip updates.

**URL:** `/gtfs/trip-updates`  
**Method:** `GET`  
**Content-Type:** `application/x-protobuf`

**Behavior:**
- Returns only active incidents (`status = active`) from the last 60 minutes.
- If `avg_delay > 30 minutes`, the stop is marked as `SKIPPED`; otherwise, `SCHEDULED`.
- Each incident is converted into a GTFS `trip_update`.

**Response:**  
Protobuf `.pb` file downloadable with `Content-Disposition: attachment`.

---

### 2. `/api/incidents` [GET]

Returns a list of recorded incidents, enriched with location names.

**URL:** `/api/incidents`  
**Method:** `GET`  
**Content-Type:** `application/json`

**Response Example:**
```
[
  {
    "id": 1,
    "location_id": 45,
    "location_name": "Trip42_Stop7",
    "type_id": 2,
    "avg_delay": 25,
    "status": "active",
    "created_at": "2025-10-05T12:00:00",
    "last_updated": "2025-10-05T12:30:00"
  }
]
```

---

### 3. `/api/reports` [GET]

Returns all reports submitted by users.

**URL:** `/api/reports`  
**Method:** `GET`  
**Content-Type:** `application/json`

**Response Example:**
```
[
  {
    "id": 101,
    "user_id": 123,
    "location_id": 45,
    "type_id": 1,
    "delay_minutes": 15,
    "incident_id": null,
    "created_at": "2025-10-05T12:01:00"
  }
]
```

---

## Architecture

- **Flask**: HTTP server exposing the endpoints.
- **Redis**: Asynchronous queue for processing reports.
- **SQLite**: Persistent storage for incidents and reports.
- **GTFS-Realtime**: Real-time export of incidents for transport integration.

---

## Notes

- `/api/incidents` and `/api/reports` return dates in UTC ISO8601 format.
- Ensure `DB_PATH` points to the correct SQLite database.
- `REDIS_HOST`, `REDIS_PORT`, and `REDIS_DB` must match your Redis configuration.

---

