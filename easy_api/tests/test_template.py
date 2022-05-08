import os

import pytest

from easy_api.template import render_template, render_string

file_dir = os.path.dirname(os.path.realpath(__file__))
template_dir = os.path.join(file_dir, 'template')


async def test_render_template():
    query, bin_params = await render_template(os.path.join(template_dir, 'hello.sql.jinja'), {'name': 'world'})
    assert query == "select ? as `name`, DATE('now') as `date`"
    assert bin_params == ['world']


async def test_render_not_exists_template():
    with pytest.raises(FileNotFoundError):
        await render_template('[not exists]', {})


async def test_render_string():
    content = "hello {{ name }}"
    query, bin_params = await render_string(content, {'name': 'world'})
    assert query == "hello ?"
    assert bin_params == ['world']


async def test_render_string_with_condition():
    content = "I'm at {{ place }} {% if yesterday %}yesterday{% endif %}"
    query, bin_params = await render_string(content, {'place': 'home', 'yesterday': True})
    assert query == "I'm at ? yesterday"
    assert bin_params == ['home']


async def test_render_string_with_like():
    content = "select * from some_table where name like {{ like_name }}"
    query, bin_params = await render_string(content, {'like_name': '%world%'})
    assert query == "select * from some_table where name like ?"
    assert bin_params == ['%world%']
