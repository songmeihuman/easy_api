import logging
import os
import sys
from dataclasses import dataclass
from typing import List

import yaml

logger = logging.getLogger("easy_api.configs")

project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass(eq=False, frozen=True)
class Server:
    """ This is about server """
    host: str
    port: int
    timezone: str
    apps: List[str]


@dataclass(eq=False, frozen=True)
class DatabaseCell:
    """ This is about database """
    name: str
    type: str
    db: str
    host: str = ""
    port: int = ""
    user: str = ""
    password: str = ""
    charset: str = ""


@dataclass(eq=False, frozen=True)
class Database:
    """ This is about database """
    instances: List[DatabaseCell]


@dataclass(eq=False, frozen=True)
class Celery:
    """ This is about celery """
    broker: str
    backend: str
    serializer: str
    timezone: str


@dataclass(eq=False, frozen=True)
class Swagger:
    """ This is about swagger """
    enable: bool
    title: str
    version: str
    description: str
    path: str
    swagger_file_path: str


server: Server
celery: Celery
database: Database
swagger: Swagger


def install(config_path: str = None):
    _config_path = os.path.join(project_root, config_path)
    if not os.path.isfile(_config_path):
        print(f"ERROR: {_config_path} was not found in {project_root}")
        sys.exit(1)

    with open(_config_path, 'r') as file:
        configs = yaml.safe_load(file)

    global server, celery, database, swagger
    server = Server(**configs["server"])
    swagger = Swagger(**configs["swagger"])
    celery = Celery(**configs["celery"])
    configs["database"]["instances"] = [
        DatabaseCell(**instance) for instance
        in configs["database"]["instances"]
    ]
    database = Database(**configs["database"])

    logger.info("loaded %s", _config_path)
