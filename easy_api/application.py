import importlib.util
import logging
from typing import Any, Tuple, List

from easy_api.seeker import Seeker, walk_apps, seek_decorator

logger = logging.getLogger("easy_api.application")

api_seeker = Seeker()


def get_api_group(name: str):
    return seek_decorator(api_seeker, name=name)


def get_handlers() -> List[Tuple[str, Any]]:
    _handlers = []

    def add_handler(api_kwargs: dict, obj: Any, url: str, order: int = 0) -> None:
        url_root = f'/{api_kwargs["name"]}' if api_kwargs.get("name") else ""
        _handlers.append((f'{url_root}{url}', obj, order))

    for item in api_seeker.pop_items():
        add_handler(item[0], item[1], *item[2], **item[3])

    handlers = [
        (x[0], x[1]) for x in
        sorted(_handlers, key=lambda x: x[2], reverse=True)
    ]

    return handlers


def install():
    """
    auto imported python file or package.
    it will autoload handler class to api_seeker when after imported.
    """
    for path in walk_apps('handler'):
        # spec = importlib.util.spec_from_file_location(path, path)
        # module = importlib.util.module_from_spec(spec)
        # spec.loader.exec_module(module)
        __import__(path[:-3].replace('/', '.'))
