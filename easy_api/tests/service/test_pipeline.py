from unittest.mock import patch

import pytest

from easy_api.handler.schema.pipeline import TaskSchema
from easy_api.schema import Result
from easy_api.service.pipeline import wrap_task, run


def async_echo(v):
    async def _(**__):
        return v

    return _


def async_require_arguments(v: Result):
    async def _(**kwargs):
        if 'required' in v.data and set(kwargs.keys()) != set(v.data['required']):
            raise ValueError("required arguments not match")
        return Result.success(kwargs)

    return _


@pytest.mark.parametrize(["data", "output", "expect", "message"], (
        (Result.success({"name": "Duo", "age": 18}), {"name": "{{ result.data.name }}"}, {"name": "Duo"}, "dict"),
        # (Result.success([{"name": "Lvy"}, {"name": "Evelyn"}]), {"names": "{{ result.data.values() }}"}, {"names": ["Lvy", "Evelyn"]}, "list"),
))
async def test_wrap_task(data, output, expect, message):
    package_name = "test"
    name = "test"
    context = {}

    with patch("easy_api.service.pipeline.get_task_by_name") as mock:
        mock.return_value = async_echo(data)
        result = await wrap_task(package_name, name, {}, output, context)
        assert result == expect, message


@pytest.mark.parametrize(["task_configs", "expect", "message"], (
        ([
             TaskSchema("", "", {"name": "Duo", "age": 18}, output={"name": "{{ result.data.name }}"}, layer=0),
             TaskSchema("", "", {"name": "Duo", "age": 18}, output={"name2": "{{ result.data.name }}"}, layer=0),
         ], {"name": "Duo", "name2": "Duo"}, "merge output to result"),
        ([
             TaskSchema("", "", {"name": "Duo", "age": 18}, output={"name": "{{ result.data.name }}"}, layer=0),
             TaskSchema("", "", {}, output={"name2": "{{ result.data.name }}"}, layer=1),
         ], {"name2": "Duo"}, "only get result from last layer"),
        ([
             TaskSchema("", "", {"name": "Duo", "age": 18}, output={"newname": "{{ result.data.name }}"}, layer=0),
             TaskSchema("", "", {}, output={"name": "{{ result.data.newname }}"}, layer=1),
         ], {"name": "Duo"}, "get result from context"),
        ([
             TaskSchema("", "", {"name": "Duo", "age": 18}, output={"newname": "{{ result.data.name }}"}, layer=0),
             TaskSchema("", "", {"name": "Duo", "age": 18}, output={"newage": "{{ result.data.age }}"}, layer=0),
             TaskSchema("", "", {},
                        output={"name": "{{ result.data.newname }}", "age": "{{ result.data.newage }}", "summary": """\"I am {{ result.data.newname }}\""""},
                        layer=1),
         ], {"name": "Duo", "age": 18, "summary": "I am Duo"}, "fan in get result"),
))
async def test_run(task_configs, expect, message):
    with patch("easy_api.service.pipeline.get_task_by_name") as mock:
        mock.return_value = async_require_arguments(Result.success({}))
        result = await run(task_configs)
        assert result == expect, message


# @pytest.mark.parametrize(["task_configs", "data", "expect", "message"], (
#         ([
#              TaskSchema("", "", {"sex": "don't care"}, output={"sex": "v(result)"}, layer=0),
#              TaskSchema("", "", {"sex": "fff"}, output={"Duo age is": "v(result).v(age)"}, layer=1),
#          ], {"name": "Duo", "age": 18, "required": ["sex"]}, TypeError,
#          "got multiple values for keyword argument 'sex'"),
#         ([
#              TaskSchema("", "", {"sex": "don't care"}, output={"sex": "just text"}, layer=0),
#              TaskSchema("", "", {}, output={"Duo age is": "v(result).v(age)"}, layer=1),
#          ], {"name": "Duo", "age": 18, "required": ["sex"]}, SyntaxError,
#          "output have invalid syntax"),
# ))
# async def test_run_with_fail(task_configs, data, expect, message):
#     with patch("easy_api.service.pipeline.get_task_by_name") as mock:
#         with pytest.raises(expect):
#             mock.return_value = async_require_arguments(data)
#             await run(task_configs)
