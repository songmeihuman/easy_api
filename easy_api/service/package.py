import logging
import os

from easy_api import configs
from easy_api.service.files import copytree_and_render

logger = logging.getLogger("easy_api.package")


async def create_package(package_name: str):
    """
    create package
    :param package_name: package name
    """
    if package_name.lower() != package_name:
        raise ValueError("package name must be lowercase")

    template_path = os.path.join(configs.project_root, "easy_api/template/package")
    package_path = os.path.join(configs.project_root, package_name)
    if os.path.exists(package_path):
        raise ValueError("package already exists")
    if not os.path.isdir(template_path):
        raise ValueError("package sql_template not exist")

    logger.debug("create package: %s", package_name)
    await copytree_and_render(template_path, package_path, {"package_name": package_name})


async def exists_package(package_name: str) -> bool:
    """
    check package exists
    """
    package_path = os.path.join(configs.project_root, package_name)
    if not os.path.exists(package_path):
        return False
    return True
