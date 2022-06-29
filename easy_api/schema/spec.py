import os
from typing import Type

import orjson
from dataclasses_jsonschema import JsonSchemaMixin
from dataclasses_jsonschema import SchemaType

VERSION = SchemaType.SWAGGER_V3


class ResponseSchemaSpec:

    def __init__(self, schema: Type[JsonSchemaMixin] = None, status_code=200, content_type="application/json"):
        self.schema = schema
        self.status_code = status_code
        self.content_type = content_type

    def apply(self, spec, operation):
        values = operation.setdefault("responses", {}).setdefault(str(self.status_code), {}).setdefault("content", {})
        values[self.content_type] = {"schema": self.schema.__name__}

        for name, schema_json in self.schema.json_schema(embeddable=True, schema_type=VERSION).items():
            if name not in spec.components.schemas:
                spec.components.schema(name, schema_json)


class RequestBodyJsonFileSpec:

    def __init__(self, name: str, schema_file: str, content_type: str = "application/json"):
        self.name = name
        self.title = os.path.split(schema_file)[1].split(".")[0]
        self.content_type = content_type
        self.schema_file = schema_file

    def apply(self, spec, operation):
        with open(self.schema_file) as f:
            schema_json = orjson.loads(f.read())

        content = operation.setdefault("requestBody", {}).setdefault("content", {})
        content[self.content_type] = {"schema": schema_json}

        # add schema to components
        # if self.title not in spec.components.schemas:
        #     spec.components.schema(self.title, schema_json)


class RequestBodySchemaSpec:

    def __init__(self, name: str, schema: Type[JsonSchemaMixin], content_type: str = "application/json"):
        self.name = name
        self.title = schema.__name__
        self.content_type = content_type
        self.schema = schema

    def apply(self, spec, operation):
        content = operation.setdefault("requestBody", {}).setdefault("content", {})
        content[self.content_type] = {"schema": self.title}

        # add schema to components
        # if self.title not in spec.components.schemas:
        #     schema_json = self.schema.json_schema(embeddable=True, schema_type=SchemaType.SWAGGER_V3)
        #     spec.components.schema(self.title, schema_json[self.title])
        for name, schema_json in self.schema.json_schema(embeddable=True, schema_type=VERSION).items():
            if name not in spec.components.schemas:
                spec.components.schema(name, schema_json)


class ParameterJsonFileSpec:

    def __init__(self, name: str, schema_file: str, parameter_type="query"):
        self.name = name
        # self.title = os.path.split(schema_file)[1].split(".")[0]
        self.schema_file = schema_file
        self.parameter_type = parameter_type

    def apply(self, spec, operation):
        parameters = operation.setdefault("parameters", [])
        with open(self.schema_file) as f:
            schema_json = orjson.loads(f.read())
        parameters.append({
            "in": self.parameter_type,
            "name": 'Datas' if self.parameter_type == "header" else "body",
            "content": {
                "application/json": {"schema": schema_json}
            }
        })


class ParameterSchemaSpec:

    def __init__(self, name: str, schema: Type[JsonSchemaMixin], parameter_type="query"):
        self.name = name
        self.title = schema.__name__
        self.schema = schema
        self.parameter_type = parameter_type

    def apply(self, spec, operation):
        parameters = operation.setdefault("parameters", [])
        schema_json = self.schema.json_schema(embeddable=True, schema_type=SchemaType.SWAGGER_V3)
        parameters.append({
            "in": self.parameter_type,
            "name": 'Datas' if self.parameter_type == "header" else "body",
            "content": {
                "application/json": {"schema": schema_json[self.title]}
            }
        })
