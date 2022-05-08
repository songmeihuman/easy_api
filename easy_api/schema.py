import json

import orjson
from fastjsonschema import compile
from jinja2schema import infer, to_json_schema, JSONSchemaDraft4Encoder
from jinja2schema.model import Unknown, Scalar

compiled_schema_validate = {}


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


def get_schema_validate(schema_file: str):
    global compiled_schema_validate
    if schema_file not in compiled_schema_validate:
        with open(schema_file, "r") as f:
            schema = orjson.loads(f.read())
        compiled_schema_validate[schema_file] = compile(schema)
    return compiled_schema_validate[schema_file]
