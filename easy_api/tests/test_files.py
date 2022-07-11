import os
import shutil

import pytest

from easy_api.service.files import read_file, copytree_and_render
from easy_api.tests.utils import assert_folders_same

file_dir = os.path.dirname(os.path.realpath(__file__))
template_dir = os.path.join(file_dir, 'template')


@pytest.fixture(scope='function')
def tmp_package():
    dst_dir = 'test_files_dst'
    try:
        yield dst_dir
    finally:

        shutil.rmtree(dst_dir)


@pytest.mark.parametrize('file_path', [
    os.path.join(template_dir, 'hello.sql.jinja'),
    os.path.join(template_dir, 'sub', 'poem.text.jinja'),
])
async def test_read_file(file_path):
    content = await read_file.__wrapped__(file_path)
    with open(file_path, 'r') as f:
        assert content == f.read()


async def test_read_not_exists_file():
    with pytest.raises(FileNotFoundError):
        await read_file.__wrapped__('[not exists]')


async def test_copytree_and_render(tmp_dst):
    context = {"name": "new"}
    await copytree_and_render(template_dir, tmp_dst, context)
    await assert_folders_same(template_dir, tmp_dst, include_template=True, template_context=context)


async def test_copytree_and_render_with_dst_exist(tmp_dst):
    context = {"name": "new"}
    os.makedirs(os.path.join(tmp_dst, 'sub'))
    await copytree_and_render(template_dir, tmp_dst, context)
    await assert_folders_same(template_dir, tmp_dst, include_template=True, template_context=context)
