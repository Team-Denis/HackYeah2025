
import os, sys
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from redis import Redis
from flask import Flask, request, Response
import json
import time
import datetime
from db import Database, IncidentRepository
from google.transit import gtfs_realtime_pb2


app = Flask(__name__)

# Configure Redis connection
redis_conn = Redis(host='localhost', port=6379, db=0)
DB_PATH = os.getenv("DB_PATH", "db/app.db")


# enqueue endpoint
@app.route('/enqueue', methods=['POST'])
def enqueue_report() -> Response:

    data: dict = request.json
    if not data:
        return {"error": "Invalid payload"}, 400
    
    try:
        redis_conn.rpush('report_queue', json.dumps(data))
    except Exception as e:
        app.logger.error(f"Redis error: {e}")
        return {"error": "Could not enqueue report"}, 500

    queue_length: int = redis_conn.llen('report_queue')
    print(f"[QUEUE] report_queue size = {queue_length}")
    return {"status": "Report enqueued", "queue_size": queue_length}, 200


@app.route('/gtfs/trip-updates')
def trip_updates():
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = '2.0'
    feed.header.timestamp = int(time.time())

    current_time = datetime.datetime.now(tz=datetime.timezone.utc)
    cutoff_time = current_time - datetime.timedelta(minutes=60)
    cutoff_time = cutoff_time.replace(tzinfo=datetime.timezone.utc)

    db = Database(DB_PATH)
    incident_repo = IncidentRepository(db)
    # Use UTC format
    incidents = incident_repo.list_incidents()
    print(f"[GTFS] Found {len(incidents)} active incidents.")
    # Process each incident and create trip updates
    for incident in incidents:
        # Only include active incidents with delays
        if incident['status'] == 'active' and incident['avg_delay'] and incident['avg_delay'] > 0:

            # Assuming location_name is formatted as "tripid_stopid"
            trip_id, stop_id = incident['location_name'].split('_')

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
            if incident['avg_delay'] > 30:  # More than 30 minutes delay
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)