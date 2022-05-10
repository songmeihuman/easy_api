import logging
import os

from easy_api import configs
from easy_api.errors import PackageExistsError, SqlExistsError, PackageNotFoundError
from easy_api.files import copytree_and_render
from easy_api.schema import get_json_schema
from easy_api.service.package import exists_package

logger = logging.getLogger("easy_api.sql")


async def create_sql(package_name: str, sql_name: str, sql_jinja: str, database: str = "default", mode: str = "execute",
                     overwrite: bool = False):
    """
    Create a sql file from a jinja template.
    :param package_name: The package name.
    :param sql_name: The sql file name.
    :param sql_jinja: The sql file content.
    :param database: The database name.
    :param mode: The sql file mode: 'execute', 'executemany', 'paginate'.
    :param overwrite: Overwrite the sql file if it already exists.
    """
    if sql_name.lower() != sql_name:
        raise ValueError("sql name must be lowercase.")

    if mode not in ('execute', 'paginate'):
        raise ValueError("sql mode must be 'execute' or 'paginate'.")

    if not await exists_package(package_name):
        raise PackageExistsError(package_name)

    template_path = os.path.join(configs.project_root, "easy_api/template/", mode)
    package_path = os.path.join(configs.project_root, package_name)
    if not os.path.isdir(template_path):
        raise ValueError("package sql_template not exist")

    if database != "default":
        for item in configs.database.instances:
            if item.name == database:
                break
        else:
            raise ValueError("database not exist")

    if not overwrite:
        if os.path.isfile(os.path.join(package_path, "handler", sql_name + ".py")):
            raise SqlExistsError(sql_name)

    sql_schema = get_json_schema(sql_jinja)

    await copytree_and_render(
        template_path,
        package_path,
        {
            "package_name": package_name,
            "sql_name": sql_name,
            "database_name": database,
            "sql_jinja": sql_jinja,
            "sql_schema": sql_schema,
        }
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
