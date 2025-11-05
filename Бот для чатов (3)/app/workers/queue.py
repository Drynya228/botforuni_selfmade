from rq import Queue
from redis import Redis
from app.core.config import cfg

redis = Redis.from_url(cfg.REDIS_URL)
queue = Queue("default", connection=redis)