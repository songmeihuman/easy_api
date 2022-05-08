import os

from easy_api.service.package import create_package, exists_package
from easy_api.tests.utils import assert_folders_same


async def test_create_package(tmp_dst):
    await create_package(tmp_dst)
    await assert_folders_same("easy_api/easy_api/template/package_template", tmp_dst,
                              include_template=True, template_context={"package_name": tmp_dst})


async def test_create_package_exists(tmp_dst):
    os.makedirs(tmp_dst)
    assert await exists_package(tmp_dst) is True
