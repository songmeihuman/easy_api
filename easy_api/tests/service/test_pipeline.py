from unittest.mock import patch

import pytest

from easy_api.handler.schema.pipeline import TaskSchema
from easy_api.service.pipeline import wrap_task, run


def async_echo(v):
    async def _(**__):
        return v

    return _


def async_require_arguments(v):
    async def _(**kwargs):
        if 'required' in v and set(kwargs.keys()) != set(v['required']):
            raise ValueError("required arguments not match")
        return v

    return _


@pytest.mark.parametrize(["data", "output", "expect", "message"], (
        ({"name": "Duo", "age": 18}, {"name": "v(result).v(name)"}, {"name": "Duo"}, "dict"),
        ([{"name": "Lvy"}, {"name": "Evelyn"}], {"names": "v(result).k(name)"}, {"names": ["Lvy", "Evelyn"]}, "list"),
))
async def test_wrap_task(data, output, expect, message):
    package_name = "test"
    name = "test"
    context = {}

    with patch("easy_api.service.pipeline.get_task_by_name") as mock:
        mock.return_value = async_echo(data)
        result = await wrap_task(package_name, name, {}, output, context)
        assert result == expect, message


@pytest.mark.parametrize(["task_configs", "data", "expect", "message"], (
        ([
             TaskSchema("", "", {}, output={"name": "v(result).v(name)"}, layer=0),
             TaskSchema("", "", {}, output={"name2": "v(result).v(name)"}, layer=0),
         ], {"name": "Duo", "age": 18}, {"name": "Duo", "name2": "Duo"}, "merge output to result"),
        ([
             TaskSchema("", "", {}, output={"name": "v(result).v(name)"}, layer=0),
             TaskSchema("", "", {}, output={"name2": "v(result).v(name)"}, layer=1),
         ], {"name": "Duo", "age": 18}, {"name2": "Duo"}, "only get result from last layer"),
        ([
             TaskSchema("", "", {}, output={"newname": "v(result).v(name)"}, layer=0),
             TaskSchema("", "", {}, output={"name": "v(newname)"}, layer=1),
         ], {"name": "Duo", "age": 18}, {"name": "Duo"}, "get result from context"),
        ([
             TaskSchema("", "", {}, output={"newname": "v(result).v(name)"}, layer=0),
             TaskSchema("", "", {}, output={"newage": "v(result).v(age).t(str)"}, layer=0),
             TaskSchema("", "", {},
                        output={"name": "v(newname)", "age": "v(newage)", "summary": """r('I am {{newname}}')"""},
                        layer=1),
         ], {"name": "Duo", "age": 18}, {"name": "Duo", "age": "18", "summary": "I am Duo"}, "fan in get result"),
        ([
             TaskSchema("", "", {"sex": "don't care"}, output={"sex": "v(result)"}, layer=0),
             TaskSchema("", "", {}, output={"Duo age is": "v(result).v(age)"}, layer=1),
         ], {"name": "Duo", "age": 18, "required": ["sex"]}, {"Duo age is": 18},
         "task output fan in to next layer task input"),
))
async def test_run(task_configs, data, expect, message):
    with patch("easy_api.service.pipeline.get_task_by_name") as mock:
        mock.return_value = async_require_arguments(data)
        result = await run(task_configs)
        assert result == expect, message


@pytest.mark.parametrize(["task_configs", "data", "expect", "message"], (
        ([
             TaskSchema("", "", {"sex": "don't care"}, output={"sex": "v(result)"}, layer=0),
             TaskSchema("", "", {"sex": "fff"}, output={"Duo age is": "v(result).v(age)"}, layer=1),
         ], {"name": "Duo", "age": 18, "required": ["sex"]}, TypeError,
         "got multiple values for keyword argument 'sex'"),
        ([
             TaskSchema("", "", {"sex": "don't care"}, output={"sex": "just text"}, layer=0),
             TaskSchema("", "", {}, output={"Duo age is": "v(result).v(age)"}, layer=1),
         ], {"name": "Duo", "age": 18, "required": ["sex"]}, SyntaxError,
         "output have invalid syntax"),
))
async def test_run_with_fail(task_configs, data, expect, message):
    with patch("easy_api.service.pipeline.get_task_by_name") as mock:
        with pytest.raises(expect):
            mock.return_value = async_require_arguments(data)
            await run(task_configs)
