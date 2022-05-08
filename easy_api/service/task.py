import functools
import logging
import os
from asyncio import Future

import aioredis
import msgpack
import tornado.ioloop
from kombu import uuid

from easy_api import configs
from easy_api.errors import PackageExistsError, PackageNotFoundError, TaskExistsError
from easy_api.files import copytree_and_render
from easy_api.service.package import exists_package
from easy_api.tasks import invoke_task

logger = logging.getLogger("easy_api.task")


async def create_task(package_name: str, task_name: str):
    """
    Create a task file from a jinja template.
    :param package_name: The package name.
    :param task_name: The task name.
    """
    if task_name.lower() != task_name:
        raise ValueError("task name must be lowercase.")

    if not await exists_package(package_name):
        raise PackageExistsError(package_name)

    template_path = os.path.join(configs.project_root, "easy_api/template/task")
    package_path = os.path.join(configs.project_root, package_name)
    if not os.path.isdir(template_path):
        raise ValueError("package task_template not exist")

    if os.path.isfile(os.path.join(package_path, "handler", task_name + ".py")):
        raise TaskExistsError(task_name)

    await copytree_and_render(
        template_path,
        package_path,
        {
            "package_name": package_name,
            "task_name": task_name,
            "legal_task_name": task_name.title().replace("_", ""),
        }
    )


async def delete_task(package_name: str, task_name: str):
    """
    Delete a task file.
    :param package_name: The package name.
    :param task_name: The task file name.
    """
    if task_name.lower() != task_name:
        raise ValueError("task name must be lowercase.")

    if not await exists_package(package_name):
        raise PackageNotFoundError(package_name)

    package_path = os.path.join(configs.project_root, package_name)
    for file_name in (f"handler/{task_name}.py", f"handler/schema/{task_name}.py", f"service/{task_name}_task.py"):
        file_path = os.path.join(package_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)


class WaitCeleryResult:
    waiter = None
    started = False

    def __init__(self):
        self.waiter = {}

    async def start(self, redis_uri):
        channel_prefix = "celery-task-meta-"
        logger.debug('start wait celery result, redis_uri: %s', redis_uri)

        redis = aioredis.from_url(redis_uri)
        async with redis.pubsub() as p:
            await p.psubscribe(channel_prefix + "*")
            while True:
                result = await p.get_message(ignore_subscribe_messages=True, timeout=10.0)
                if result is None:
                    continue

                try:
                    result = msgpack.unpackb(result['data'])
                    f = self.waiter.pop(result['task_id'], None)
                    if f:
                        f.set_result(result['result'])
                except Exception as e:
                    logger.exception("result: %s, error: %s", result, e)

    def subscribe(self, task_id, callback):
        self.waiter[task_id] = callback
        if not self.started:
            self.started = True
            redis_url = configs.celery.backend
            tornado.ioloop.IOLoop.current().add_callback(wait_celery_result.start, redis_url)


wait_celery_result = WaitCeleryResult()


def run_in_worker(package_name: str, task_name: str):
    def _(func):
        @functools.wraps(func)
        async def _fun_in_worker(*args, **kwargs):
            worker_task_id = uuid()
            future = Future()
            wait_celery_result.subscribe(worker_task_id, future)

            invoke_task.apply_async(args=[package_name, task_name, args, kwargs], task_id=worker_task_id,
                                    ignore_result=False)
            result = await future
            return result

        return _fun_in_worker

    return _
