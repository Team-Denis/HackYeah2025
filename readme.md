# HackYeah2025 API

This API provides a real-time incident reporting system with GTFS-Realtime integration and Redis/SQLite storage. It allows submitting reports, fetching incidents, and generating real-time trip updates.

---

## Configuration


### 1. Cloudflare
Create a Cloudflare tunnel with two routes towards `http://otp:8080` and `http://flask-backend:5000`

Then, copy your token in the `.env` file

### 2. OTP
Make sure `java 17` or later is installed on your system.

Download the `.jar` file from opentripplanner, your GTFS files and your PBF files and build the graph :

```
java -Xmx2G -jar otp.jar --build --save .
```

### 3. Docker

Make sure `docker` and `docker compose` are installed on your machine.

You can now run the containers by using :

```
docker-compose up -d --build
```


---

## Endpoints

### 1. `/enqueue` [POST]

Submits a user report to the Redis queue for asynchronous processing.

**Request JSON:**
```json
{
    "location_id": 101,
    "type_id": 1,
    "trust_score": 0.8,
    "avg_delay": 12.0,
    "status": "active"
}
```

Response JSON:

```
{
    "status": "Report enqueued",
    "queue_size": 3
}
```

### 2. `/gtfs/trip-updates` [GET]

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

### 3. `/api/incidents` [GET]

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

### 4. `/api/reports` [GET]

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
### 5. '/api/incidents/<incident_id/reports>' [GET]
Returns all reports associated with a specific incident.
# Response Example:

```
[
  {
    "id": 102,
    "user_id": 124,
    "location_id": 45,
    "type_id": 1,
    "delay_minutes": 10,
    "incident_id": 1,
    "created_at": "2025-10-05T12:05:00"
  }
]
```

### 6. '/api/types' [GET]
Returns all available type mappings ```(type_id → type_name)```.

# Response Example:
```
[
  {
    "id": 1,
    "name": "Delay"
  },
  {
    "id": 2,
    "name": "Accident"
  }
]
```

### 7. '/api/locations' [GET]
Returns all available location mappings ```(location_id → location_name)```.

# Response Example:

```json
[
  {
    "id": 101,
    "name": "Trip42_Stop7",
    "latitude": 52.2297,
    "longitude": 21.0122
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

