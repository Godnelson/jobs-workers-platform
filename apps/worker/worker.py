from redis import Redis
from rq import Connection, Queue, Worker

from apps.api.settings import load_settings
from apps.api.logging import configure_logging


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    redis = Redis.from_url(settings.redis_url, decode_responses=False)
    q = Queue(settings.rq_queue_name, connection=redis)

    with Connection(redis):
        w = Worker([q], name="worker-1")
        w.work(with_scheduler=False)


if __name__ == "__main__":
    main()
