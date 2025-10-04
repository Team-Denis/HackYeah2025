from redis import Redis

class EventHandler:

    def __init__(self, handler_func):
        self.redis_conn = Redis(host='localhost', port=6379, db=0)
        self.pubsub = self.redis_conn.pubsub()
        self.pubsub.subscribe("event_queue")
        self.handler_func = handler_func

    def listen_and_handle(self):
        for message in self.pubsub.listen():
            self.handler_func(message)
    


if __name__ == "__main__":

    def func(mess):
        print("Received Message: ", mess)

    handler = EventHandler(func)

    handler.listen_and_handle()