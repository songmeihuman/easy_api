import logging
import os
from typing import List

from easy_api import configs
from easy_api.errors import SqlExistsError, PackageNotFoundError
from easy_api.files import copytree_and_render
from easy_api.schema import get_json_schema
from easy_api.service.package import exists_package

logger = logging.getLogger("easy_api.sql")


def common_pre_checker(package_name: str, sql_name: str, overwrite: bool, database: str = "default"):
    if sql_name.lower() != sql_name:
        raise ValueError("sql name must be lowercase.")

    if not exists_package(package_name):
        raise PackageNotFoundError(package_name)

    if database != "default":
        for item in configs.database.instances:
            if item.name == database:
                break
        else:
            raise ValueError("database not exist")

    package_path = os.path.join(configs.project_root, package_name)
    if not overwrite:
        if os.path.isfile(os.path.join(package_path, "handler", sql_name + ".py")):
            raise SqlExistsError(sql_name)


def wrap_count_sql(sql: str) -> str:
    return "select count(*) as `count` from ({}) as _count".format(sql)


async def create_sql(package_name: str, sql_name: str, sql_jinja: str,
                     database: str = "default", overwrite: bool = False):
    common_pre_checker(package_name, sql_name, overwrite, database)

    package_path = os.path.join(configs.project_root, package_name)
    template_path = os.path.join(configs.project_root, "easy_api/template/execute")
    if not os.path.isdir(template_path):
        raise ValueError("package sql_template not exist")

    render_context = {
        "package_name": package_name,
        "sql_name": sql_name,
        "database_name": database,
        "sql_jinja": sql_jinja,
        "sql_schema": get_json_schema(sql_jinja),
    }

    await copytree_and_render(
        template_path,
        package_path,
        render_context,
    )


async def create_paging_sql(package_name: str, sql_name: str, sql_jinja: str, count_jinja: str,
                            database: str = "default", overwrite: bool = False):
    """
    Create a paging sql file from a jinja template.
    :param package_name: The package name.
    :param sql_name: The sql file name.
    :param sql_jinja: The sql file content.
    :param count_jinja: The count sql file content.
    :param database: The database name.
    :param overwrite: Overwrite the sql file if it already exists.
    """
    common_pre_checker(package_name, sql_name, overwrite, database)

    package_path = os.path.join(configs.project_root, package_name)
    template_path = os.path.join(configs.project_root, "easy_api/template/paging")
    if not os.path.isdir(template_path):
        raise ValueError("package sql_template not exist")

    # add page and page_size to sql_jinja
    paging_sql_jinja = "{% set _page = page|default(1) %} {% set _page_size = page_size|default(10) %}\n" \
                       f"{sql_jinja}" \
                       " limit {{ _page }} offset {{ _page_size * (_page - 1) }}"

    if not count_jinja:
        # wrap sql to count sql
        count_jinja = f"select count(*) as `count` from ({sql_jinja}) as _count"

    render_context = {
        "package_name": package_name,
        "sql_name": sql_name,
        "database_name": database,
        "sql_jinja": paging_sql_jinja,
        "count_jinja": count_jinja,
        "sql_schema": get_json_schema(paging_sql_jinja),
    }

    await copytree_and_render(
        template_path,
        package_path,
        render_context,
    )


async def delete_sql(package_name: str, sql_name: str):
    """
    Delete a sql file.
    :param package_name: The package name.
    :param sql_name: The sql file name.
    """
    if sql_name.lower() != sql_name:
        raise ValueError("sql name must be lowercase.")

    if not await exists_package(package_name):
        raise PackageNotFoundError(package_name)

    package_path = os.path.join(configs.project_root, package_name)
    for file_name in (f"handler/{sql_name}.py", f"handler/schema/{sql_name}.json", f"service/{sql_name}_sql.py",
                      f"service/sql_template/{sql_name}.sql.jinja"):
        file_path = os.path.join(package_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)


async def list_sql(package_name: str) -> List[str]:
    return []
