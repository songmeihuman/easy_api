import asyncio
from typing import List, Dict

from easy_api.handler.schema.pipeline import TaskSchema
from easy_api.service import trim_output
from easy_api.tasks import get_task_by_name


async def wrap_task(package_name, name, inputs, output, context):
    # FIXME hard to debug
    job = get_task_by_name(package_name, name)
    result = await job(**inputs, **context)
    return trim_output.process({"result": result}, output, context)


async def run(task_configs: List[TaskSchema]):
    """
    Create a group file from a jinja template.
    :param task_configs: The task inputs.
    """
    task_dicts: Dict[int, List[TaskSchema]] = {}
    for task in task_configs:
        task_dicts.setdefault(task.layer, []).append(task)

    results = {}

    for layer in range(5):
        if layer not in task_dicts:
            break

        tasks = (wrap_task(x.package_name, x.name, x.kwargs, x.output, results) for x in task_dicts[layer])
        results = await asyncio.gather(*tasks)
        results = {k: v for d in results for k, v in d.items()}

    return results
