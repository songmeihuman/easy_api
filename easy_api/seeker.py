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


def walk_apps(name: str):
    for app_name in configs.server.apps:
        file_path = os.path.join(app_name, f'{name}.py')
        may_be_folder = os.path.join(app_name, name)

        if os.path.isfile(file_path):
            # only file
            yield file_path
        elif os.path.isdir(may_be_folder):
            # there are many file in this package
            yield from glob.iglob(may_be_folder + '/**/*.py', recursive=True)
        else:
            # not found
            continue


def seek_decorator(seeker: Seeker, **api_kwargs):
    def _seek_decorator(*args, **kwargs):
        def inner(obj):
            seeker.add_item(api_kwargs, obj, args, kwargs)
            return obj

        return inner

    return _seek_decorator
