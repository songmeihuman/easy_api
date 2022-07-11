import logging
from asyncio import Future

import aioredis
import msgpack
import orjson
import tornado.ioloop
from celery.result import AsyncResult

from easy_api import configs

logger = logging.getLogger("easy_api.redis_waiter")

is_redis_backend = True
waiter = {}


async def start_watch(redis_url):
    channel_prefix = "celery-task-meta-"

    redis = aioredis.from_url(redis_url)
    async with redis.pubsub() as p:
        await p.psubscribe(channel_prefix + "*")
        while True:
            result = await p.get_message(ignore_subscribe_messages=True, timeout=10.0)
            if result is None:
                continue

            try:
                if configs.celery.serializer == 'msgpack':
                    result = msgpack.unpackb(result['data'])
                elif configs.celery.serializer == 'json':
                    result = orjson.loads(result['data'])
                else:
                    logger.warning("unknown serializer: %s", configs.celery.serializer)
                    result = result['data']

                f = waiter.pop(result['task_id'], None)
                if f:
                    f.set_result(result['result'])
            except Exception as e:
                logger.exception("result: %s, error: %s", result, e)


def wait_result(task_id: str, future: Future):
    """ wait task_id result and then call callback with result """
    if is_redis_backend:
        waiter[task_id] = future
    else:
        result = AsyncResult(task_id).get()
        future.set_result(result)


def install():
    redis_url = configs.celery.backend
    if redis_url.startswith("redis://"):
        tornado.ioloop.IOLoop.current().add_callback(start_watch, redis_url)
        logger.debug('start celery waiter, redis_uri: %s', redis_url)
    else:
        global is_redis_backend
        is_redis_backend = False
        logger.warning("redis url: %s not start with redis://", redis_url)
