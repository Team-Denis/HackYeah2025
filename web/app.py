from redis import Redis
from flask import Flask, request

app = Flask(__name__)

# Configure Redis connection
redis_conn = Redis(host='localhost', port=6379, db=0)

@app.route('/enqueue', methods=['POST'])
def enqueue_event():
    data = request.json
    if not data:
        return {"error": "Invalid payload"}, 400
    
    redis_conn.publish('event_queue', str(data))
    return {"status": "Event enqueued"}, 200



if __name__ == "__main__":
    app.run()