'''import redis


class Connection:
    conn = ""
    def __init__(self):
        self.conn = redis.Redis(
            host='localhost',
            port="6379",
            )'''
            
import redis
import os

class Connection:
    conn = ""
    def __init__(self):
        self.conn = redis.from_url(os.environ.get("REDIS_URL"))
        



        

