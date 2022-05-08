import os

import pytest
import tornado.httpclient
import tornado.web

from easy_api import configs
from easy_api.handler.package import CreatePackageHandler
from easy_api.tests.utils import assert_folders_same, assert_result
from easy_api.web import Result


@pytest.fixture
def app():
    return tornado.web.Application([
        (r"/package/create/(\w+)", CreatePackageHandler),
    ])


async def test_create_package(http_server_client, tmp_dst):
    response = await http_server_client.fetch(f'/package/create/{tmp_dst}', method="POST", body="{}")
    assert_result(response, 200, Result.success('ok'))

    await assert_folders_same("easy_api/easy_api/template/package_template", tmp_dst,
                              include_template=True, template_context={"package_name": tmp_dst})


async def test_create_package_with_exists_package(http_server_client, tmp_dst):
    os.makedirs(os.path.join(configs.project_root, tmp_dst))
    response = await http_server_client.fetch(f'/package/create/{tmp_dst}', method="POST", body="{}")
    assert_result(response, 200, Result.failre('package already exists', -1))


async def test_create_package_with_invalid_name(http_server_client):
    with pytest.raises(tornado.httpclient.HTTPClientError, match="HTTP 400"):
        await http_server_client.fetch(f'/package/create/no no', method="POST", body="{}")

    with pytest.raises(tornado.httpclient.HTTPClientError, match="HTTP 404"):
        await http_server_client.fetch(f'/package/create/no%20no', method="POST", body="{}")

    with pytest.raises(tornado.httpclient.HTTPClientError, match="HTTP 404"):
        await http_server_client.fetch(f'/package/create/$%#*', method="POST", body="{}")

    response = await http_server_client.fetch(f'/package/create/Capital', method="POST", body="{}")
    assert_result(response, 200, Result.failre('package name must be lowercase', -1))
