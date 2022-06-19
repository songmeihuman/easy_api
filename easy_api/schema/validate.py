import logging
from typing import Type, Any

import dataclasses_jsonschema
import orjson
from dataclasses_jsonschema import JsonSchemaMixin
from fastjsonschema import compile, JsonSchemaException

log = logging.getLogger("easy_api.schema")
compiled_schema_validate = {}

def get_schema_validate(schema_file: str):
    global compiled_schema_validate
    if schema_file not in compiled_schema_validate:
        with open(schema_file, "r") as f:
            schema = orjson.loads(f.read())
        compiled_schema_validate[schema_file] = compile(schema)
    return compiled_schema_validate[schema_file]


async def validate_with_schema_class(data: dict, schema: Type[JsonSchemaMixin]) -> (str, Any):
    try:
        result = schema.from_dict(data)
    except dataclasses_jsonschema.ValidationError as e:
        if logging.DEBUG >= logging.root.level:
            log.exception(
                "request schema validation error, json_data is %s, schema is %s", data, schema)
        return str(e), None

    return "", result


async def validate_with_schema_file(data: dict, schema_file: str) -> (str, Any):
    schema_validate = get_schema_validate(schema_file)
    try:
        schema_validate(data)
    except JsonSchemaException as e:
        if logging.DEBUG >= logging.root.level:
            log.exception(
                "request schema validation error, json_data is %s, schema is %s", data, schema_file)
        return e.message, None

    return "", data
