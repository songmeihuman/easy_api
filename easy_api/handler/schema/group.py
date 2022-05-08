from dataclasses import dataclass, field
from typing import List

from dataclasses_jsonschema import JsonSchemaMixin


@dataclass
class TaskSchema(JsonSchemaMixin):
    """ Task Schema """
    package_name: str = field(metadata={"description": "The package name"})
    name: str = field(metadata={"description": "The sql name or task name"})
    kwargs: dict = field(metadata={"description": "The default params will be pass to the task"})
    output: dict = field(metadata={"description": "The output of the task"})
    layer: int = field(metadata={"description": "Synchronous execution in layer order"}, default=0)


@dataclass
class GroupRequestSchema(JsonSchemaMixin):
    """ The request schema for group """
    tasks: List[TaskSchema]
