import asyncio
import os.path
import shutil

import pytest

from easy_api import configs
from easy_api.errors import SqlExistsError
from easy_api.schema import get_json_schema
from easy_api.service.package import create_package
from easy_api.service.sql import create_sql, delete_sql
from easy_api.tests.utils import assert_folders_same


@pytest.fixture(scope='function')
def tmp_package():
    dst_dir = 'test_package'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_package(dst_dir))
    try:
        yield dst_dir
    finally:
        real_dst_dir = os.path.join(configs.project_root, dst_dir)
        if os.path.exists(real_dst_dir):
            shutil.rmtree(real_dst_dir)


async def create_test_sql(tmp_package,
                          sql_name="select_name",
                          sql_jinja="select {{ name }} as `name`",
                          mode="execute",
                          overwrite=True
                          ):
    await create_sql(tmp_package, sql_name, sql_jinja, mode, overwrite)


async def test_create_execute_sql(tmp_package):
    sql_name = "select_name"
    sql_jinja = "select {{ name }} as `name`"
    await create_test_sql(tmp_package, sql_name=sql_name, sql_jinja=sql_jinja)

    sql_schema = get_json_schema(sql_jinja)
    await assert_folders_same("easy_api/easy_api/template/execute", tmp_package,
                              include_template=True,
                              template_context={
                                  "package_name": tmp_package,
                                  "sql_name": sql_name,
                                  "sql_jinja": sql_jinja,
                                  "sql_schema": sql_schema,
                              })


async def test_create_with_exists_package(tmp_package):
    await create_test_sql(tmp_package)
    with pytest.raises(SqlExistsError):
        await create_test_sql(tmp_package, overwrite=False)


async def test_delete_sql(tmp_package):
    sql_name = "select_name"
    await create_test_sql(tmp_package, sql_name=sql_name)
    await delete_sql(tmp_package, sql_name)

    assert not os.path.exists(os.path.join(configs.project_root, tmp_package, "handler", f"{sql_name}.py"))
    assert not os.path.exists(os.path.join(configs.project_root, tmp_package, "handler", "schema", f"{sql_name}.json"))
    assert not os.path.exists(os.path.join(configs.project_root, tmp_package, "service", f"{sql_name}_sql.py"))
    assert not os.path.exists(
        os.path.join(configs.project_root, tmp_package, "service", "sql_template", f"{sql_name}.sql.jinja"))
