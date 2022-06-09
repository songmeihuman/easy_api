import logging
from dataclasses import asdict
from importlib import import_module

from celery import shared_task

logger = logging.getLogger("easy_api.queue")


def get_task_by_name(package_name, name):
    module = import_module(f'{package_name}.service.{name}')
    return getattr(module, 'run', None)


@shared_task
def invoke_task(package_name, task_name, args, kwargs):
    """
    Invoke a task in a package.
    """
    task = get_task_by_name(package_name, task_name)
    if task is None:
        logger.error("Task not found: %s.%s", package_name, task_name)
        return

    try:
        result = task.__wrapped__(*args, **kwargs)
        return asdict(result)
    except Exception as e:
        logger.exception(e)
