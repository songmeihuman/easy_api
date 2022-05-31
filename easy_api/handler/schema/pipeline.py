from dataclasses import dataclass, field
from typing import List

from dataclasses_jsonschema import JsonSchemaMixin


@dataclass
class TaskSchema(JsonSchemaMixin):
    """ Task Schema """
    package_name: str = field(metadata={"description": "The package name"})
    name: str = field(metadata={"description": "The sql name or task"})
    kwargs: dict = field(metadata={"description": "The default params will be pass to the task"})
    output: dict = field(metadata={"description": "The output of the task"})
    condition: str = field(metadata={"description": "The condition of task, jinja2 template syntax"}, default="")
    layer: int = field(metadata={"description": "Synchronous execution in layer order"}, default=0)


@dataclass
class PipelineRequestSchema(JsonSchemaMixin):
    """ The request schema for group """
    tasks: List[TaskSchema]
    version: str = field(metadata={"description": "The version of the pipeline"}, default="v1")
