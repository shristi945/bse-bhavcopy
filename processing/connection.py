import redis


class Connection:
    conn = ""
    def __init__(self):
        self.conn = redis.Redis(
            host='localhost',
            port="6379",
            )
