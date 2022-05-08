from typing import Tuple

from jinjasql import JinjaSql

from .files import read_file


async def render_template(template_path: str, params: dict) -> Tuple[str, list]:
    template = await read_file(template_path)
    return await render_string(template, params)


async def render_string(text: str, params: dict) -> Tuple[str, list]:
    j = JinjaSql(param_style="qmark")
    query, bind_params = j.prepare_query(text, params)
    return query, bind_params
