import json
import logging
from enum import Enum
from typing import Any

import orjson
from jinja2schema import infer, to_json_schema, JSONSchemaDraft4Encoder
from jinja2schema.model import Unknown, Scalar

log = logging.getLogger("easy_api.schema")


class Parameters(Enum):
    QUERY = "__query_schema__"
    PATH = "__path_schema__"
    HEADER = "__header_schema__"


class MyJSONSchemaDraft4Encoder(JSONSchemaDraft4Encoder):
    """Encodes :class:`.model.Unknown` and :class:`.model.Scalar` (but not it's subclasses --
    :class:`.model.String`, :class:`.model.Number` or :class:`.model.Boolean`) variables as strings.

    Useful for rendering forms using resulting JSON schema, as most of form-rendering
    tools do not support "anyOf" validator.
    """

    def encode(self, var):
        if isinstance(var, Unknown):
            rv = self.encode_common_attrs(var)
            rv['type'] = 'boolean'
        elif type(var) is Scalar:
            rv = self.encode_common_attrs(var)
            rv['type'] = 'string'
        else:
            rv = super(MyJSONSchemaDraft4Encoder, self).encode(var)
        return rv


def get_json_schema(sql_jinja: str):
    """
    Converts SQL Jinja to JSON Schema.
    """
    schema = to_json_schema(infer(sql_jinja), MyJSONSchemaDraft4Encoder)
    return json.dumps(schema, indent=2)


def safe_load_json(text: str) -> (bool, Any):
    if not text:
        return False, None

    try:
        json_data = orjson.loads(text)
    except ValueError:
        try:
            json_data = orjson.loads(
                text.replace(b'\\\\', b'\\')
            )
        except ValueError:
            if logging.DEBUG >= logging.root.level:
                log.exception("request body is invalid json data", text)
            return False, None

    return True, json_data


def is_successful_result(result) -> bool:
    """check if result is successful"""
    return result.code == 0
