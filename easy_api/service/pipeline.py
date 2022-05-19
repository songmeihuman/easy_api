import asyncio
import logging
from ast import literal_eval
from dataclasses import asdict
from typing import List, Dict

from jinja2 import Template

from easy_api.handler.schema.pipeline import TaskSchema
from easy_api.schema import is_successful_result
from easy_api.tasks import get_task_by_name

logger = logging.getLogger("easy_api.pipeline")


def execute_inline_template(text: str, context: dict) -> any:
    """
    Execute a template in a string.
    :param text: The template string.
    :param context: The context.
    """
    value = Template(text).render(context)
    if not value:
        return ""

    try:
        return literal_eval(value)
    except ValueError:
        # this is a hack to handle the case where the value type is a string
        return literal_eval(f"""'{value}'""")


def execute_condition_template(condition: str, context: dict) -> bool:
    if condition == "":
        return True
    return True if execute_inline_template(condition, context) else False


async def wrap_task(package_name, name, inputs, output, context):
    # FIXME hard to debug
    if not output:
        # It not wants to save the result
        return {}

    job = get_task_by_name(package_name, name)
    result = await job(**inputs, **context)
    if is_successful_result(result):
        result = asdict(result)
        return {k: execute_inline_template(v, {"result": result}) for k, v in output.items()}
    else:
        for key in output:
            return {f"{key}_error": result}


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

        tasks = (
            wrap_task(x.package_name, x.name, x.kwargs, x.output, results)
            for x in task_dicts[layer]
            if execute_condition_template(x.condition, results)
        )
        results = await asyncio.gather(*tasks)
        results = {k: v for d in results for k, v in d.items()}

    return results
