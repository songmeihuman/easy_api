import os

import orjson
from jinja2 import Template


async def assert_folders_same(src_root_path: str, dst_root_path: str, include_template: bool = True,
                              template_context: dict = None):
    """ assert that two folders are the same, include jinja2 template """
    if template_context is None:
        template_context = {}

    for root, dirs, files in os.walk(src_root_path):
        for file in files:
            src = os.path.join(root, file)
            dst = src.replace(src_root_path, dst_root_path)
            if include_template and dst.endswith('.jinja'):
                assert not os.path.isfile(dst), dst
                dst, _ = os.path.splitext(dst)
                if '{{' in dst:
                    dst = Template(dst).render(**template_context)
            assert os.path.isfile(dst), dst

        for dir_ in dirs:
            src = os.path.join(root, dir_)
            dst = src.replace(src_root_path, dst_root_path)
            assert os.path.isdir(dst), dst


def assert_result(response, code, result):
    """ test response code and result """
    assert response.code == code
    assert response.body == orjson.dumps(result)
