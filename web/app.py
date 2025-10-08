
import os, sys
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from redis import Redis
from flask import Flask, request, Response
import json
import time
import datetime
from dotenv import load_dotenv
from db import Database, IncidentRepository, GeneralRepository, ReportRepository
from google.transit import gtfs_realtime_pb2
from typing import List, Dict, Any


app = Flask(__name__)
load_dotenv()


# Configure Redis connection
redis_conn = Redis(host=os.getenv("REDIS_HOST", "redis"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))
TIME_THRESHOLD_MINUTES = 60  # 1 hour
SEVERITY_THRESHOLD_MINUTES = 30  # 30 minutes


# enqueue endpoint
@app.route('/enqueue', methods=['POST'])
def enqueue_report() -> Response:

    data: dict = request.json
    if not data:
        return {"error": "Invalid payload"}, 400
    
    print(data)
    
    try:
        redis_conn.rpush('report_queue', json.dumps(data))
    except Exception as e:
        app.logger.error(f"Redis error: {e}")
        return {"error": "Could not enqueue report"}, 500

    queue_length: int = redis_conn.llen('report_queue')
    print(f"[QUEUE] report_queue size = {queue_length}")
    return {"status": "Report enqueued", "queue_size": queue_length}, 200


# GTFS-Realtime Trip Updates endpoint
@app.route('/gtfs/trip-updates', methods=['GET'])
def trip_updates() -> None:

    db: Database = Database(os.getenv("DB_PATH"))  # ugly but works for now

    feed: gtfs_realtime_pb2.FeedMessage = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = '2.0'
    feed.header.timestamp = int(time.time())  # ?? might need to use UTC time

    current_time: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)
    cutoff_time: datetime.datetime = (current_time - datetime.timedelta(minutes=TIME_THRESHOLD_MINUTES)
                   ).replace(tzinfo=datetime.timezone.utc)

    incident_repo: IncidentRepository = IncidentRepository(db)
    general_repo: GeneralRepository = GeneralRepository(db)
    incidents: List[Dict[str, Any]] = incident_repo.get_incidents_since(cutoff_time)

    print(f"[GTFS] Found {len(incidents)} active incidents.")

    # Process each incident and create trip updates
    for incident in incidents:

        # Only include active incidents with delays
        if not incident['avg_delay']:
            incident['avg_delay'] = TIME_THRESHOLD_MINUTES  # Default to 60 minutes if None
            
        if incident['status'] == 'active' and incident['avg_delay'] > 0:

            # Assuming location_name is formatted as "tripid_stopid"
            location_id = incident.get('location_id')
            location = general_repo.get_location_by_id(location_id)
            trip_id, stop_id = location['name'].split('@')

            print(f"Processing incident {incident['id']} for trip {trip_id} at stop {stop_id}")

            # Create a new trip update entity
            entity = feed.entity.add()
            entity.id = f"incident_{incident['id']}"
            
            # Create trip update
            trip_update = entity.trip_update
            
            # Set trip information - you'll need to map location_id to actual trip_id
            # This depends on your GTFS data structure
            trip_update.trip.trip_id = trip_id
            
            # Add stop time update
            stop_time_update = trip_update.stop_time_update.add()
            stop_time_update.stop_id = stop_id
            
            # Set delay in seconds (avg_delay is presumably in minutes)
            delay_seconds = int(incident['avg_delay'] * 60)
            stop_time_update.arrival.delay = delay_seconds
            stop_time_update.departure.delay = delay_seconds
            
            # Set schedule relationship based on severity
            if incident['avg_delay'] > SEVERITY_THRESHOLD_MINUTES:  # More than 30 minutes delay
                stop_time_update.schedule_relationship = stop_time_update.SKIPPED
            else:
                stop_time_update.schedule_relationship = stop_time_update.SCHEDULED

    # Serialize and return the feed
    response = Response(
        feed.SerializeToString(),
        mimetype='application/x-protobuf',
        headers={
            'Content-Disposition': 'attachment; filename=trip_updates.pb'
        }
    )
    return response


# Public API endpoint to get all incidents with enriched location names
@app.route('/api/incidents', methods=['GET'])
def get_incidents() -> Response:

    db: Database = Database(os.getenv("DB_PATH"))  # ugly but works for now
    incident_repo: IncidentRepository = IncidentRepository(db)
    general_repo: GeneralRepository = GeneralRepository(db)
    incidents: List[Dict[str, Any]] = incident_repo.list_incidents()

    # Enrich incidents with location names
    for incident in incidents:
        location_id = incident.get('location_id')
        if location_id:
            location = general_repo.get_location_by_id(location_id)
            incident['location_name'] = location['name'] if location else 'Unknown'
        else:
            incident['location_name'] = 'Unknown'

    return Response(
        json.dumps(incidents, default=str),  # default=str to handle datetime serialization
        mimetype='application/json'
    )


# Public API endpoint to get all reports ever made
@app.route('/api/reports', methods=['GET'])
def get_reports() -> Response:

    db: Database = Database(os.getenv("DB_PATH"))  # ugly but works for now
    report_repo: ReportRepository = ReportRepository(db)
    reports: List[Dict[str, Any]] = report_repo.list_reports()

    return Response(
        json.dumps(reports, default=str),  # default=str to handle datetime serialization
        mimetype='application/json'
    )


# related reports to an incident endpoint
@app.route('/api/incidents/<int:incident_id>/reports', methods=['GET'])
def get_incident_reports(incident_id: int) -> Response:

    db: Database = Database(os.getenv("DB_PATH"))  # ugly but works for now
    report_repo: ReportRepository = ReportRepository(db)
    reports: List[Dict[str, Any]] = report_repo.get_reports_by_incident(incident_id)

    return Response(
        json.dumps(reports, default=str),  # default=str to handle datetime serialization
        mimetype='application/json'
    )


# type id to name mapping endpoint
@app.route('/api/types', methods=['GET'])
def get_types() -> Response:

    db: Database = Database(os.getenv("DB_PATH"))  # ugly but works for now
    general_repo: GeneralRepository = GeneralRepository(db)
    types: List[Dict[str, Any]] = general_repo.list_types()
    return Response(
        json.dumps(types, default=str),  # default=str to handle datetime serialization
        mimetype='application/json'
    )


# location id to name mapping endpoint
@app.route('/api/locations', methods=['GET'])
def get_locations() -> Response:

    db: Database = Database(os.getenv("DB_PATH"))  # ugly but works for now
    general_repo: GeneralRepository = GeneralRepository(db)
    locations: List[Dict[str, Any]] = general_repo.list_locations()
    return Response(
        json.dumps(locations, default=str),  # default=str to handle datetime serialization
        mimetype='application/json'
    )


if __name__ == "__main__":
    
    app.run(host=os.getenv("HOST"), port=os.getenv("PORT"), debug=True)

