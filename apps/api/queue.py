from redis import Redis
from rq import Queue


def get_queue(redis_url: str, queue_name: str) -> Queue:
    redis = Redis.from_url(redis_url, decode_responses=True)
    return Queue(name=queue_name, connection=redis)
