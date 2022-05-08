import glob
import os
from typing import Dict, Any, Tuple

from easy_api import configs


class Seeker:
    items = None

    def __init__(self):
        self.items = []

    def add_item(self, api_kwargs: dict, obj: Any, args: Tuple, kwargs: Dict):
        self.items.append((api_kwargs, obj, args, kwargs))

    def get_items(self):
        return self.items

    def pop_items(self):
        items = self.items
        self.items = []
        return items

    def new_decorator(self, **kwargs):
        return seek_decorator(self, **kwargs)


def walk_apps(package_name: str):
    for app_name in configs.server.apps:
        package_file_path = os.path.join(app_name, f'{package_name}.py')
        package_path = os.path.join(app_name, package_name)

        if os.path.isfile(package_file_path):
            # only file
            yield package_file_path
        elif os.path.isdir(package_path):
            # there are many file in this package
            yield from glob.iglob(package_path + '/**/*.py', recursive=True)
        else:
            # not find
            continue


def seek_decorator(seeker: Seeker, **api_kwargs):
    def _seek_decorator(*args, **kwargs):
        def inner(obj):
            seeker.add_item(api_kwargs, obj, args, kwargs)
            return obj

        return inner

    return _seek_decorator
