
import os, sys
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from redis import Redis
from flask import Flask, request, Response
import json


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)