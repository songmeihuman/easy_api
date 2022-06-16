import functools
import json
import logging
from dataclasses import dataclass, field
from typing import Union, Type, Any

import dataclasses_jsonschema
import orjson
import tornado.web
from dataclasses_jsonschema import JsonSchemaMixin
from fastjsonschema import compile, JsonSchemaException
from jinja2schema import infer, to_json_schema, JSONSchemaDraft4Encoder
from jinja2schema.model import Unknown, Scalar

from easy_api.web import logger, Handler

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


@dataclass
class Result(JsonSchemaMixin):
    """ this is  a result """

    code: int = field(metadata={"description": "my code here"}, default=0)
    msg: str = ""
    data: Union[dict, list, str, int] = None

    @classmethod
    def error(cls, error: Exception, code: int = -1):
        return cls(code=code, msg=str(error))

    @classmethod
    def success(cls, data: Union[dict, list, str]):
        return cls(code=0, data=data)

    @classmethod
    def failre(cls, msg: str, code: int = -1):
        return cls(code=code, msg=msg)


@dataclass
class SqlResult(JsonSchemaMixin):
    code: int = 0
    msg: str = ""
    data: Union[dict, list, str, int] = None
    changes: int = 0

    @classmethod
    def success(cls, data: Union[dict, list, str], changes: int):
        return cls(code=0, data=data, changes=changes)

    @classmethod
    def error(cls, error: Exception, code: int = -1):
        return cls(code=code, msg=str(error))

    @classmethod
    def failre(cls, msg: str, code: int = -1):
        return cls(code=code, msg=msg)


@dataclass
class SqlPagingResult(JsonSchemaMixin):
    code: int = 0
    msg: str = ""
    data: Union[dict, list, str, int] = None
    count: int = 0

    @classmethod
    def success(cls, data: Union[dict, list, str], count: int):
        return cls(code=0, data=data, count=count)

    @classmethod
    def error(cls, error: Exception, code: int = -1):
        return cls(code=code, msg=str(error))

    @classmethod
    def failre(cls, msg: str, code: int = -1):
        return cls(code=code, msg=msg)


def is_successful_result(result) -> bool:
    return result.code == 0


def response_schema(schema: Type[JsonSchemaMixin] = None, status_code=200, content="application/json", description=""):
    """
    1. response schema can helper render swagger schema file
    2. auto write json response from method return value
    :param schema: the schema class
    :param status_code: the status code for response, default is 200
    :param content: the content type for response, default is application/json
    :param description: description for schema
    :return:
    """

    def _(func):
        _schema = getattr(func, '__response_schema__', {})
        _schema[status_code] = {"content": content, "description": description, "schema": schema}
        setattr(func, '__response_schema__', _schema)

        @functools.wraps(func)
        async def inner_response_schema(self: Handler, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            if isinstance(result, JsonSchemaMixin):
                self.write(result)

        return inner_response_schema

    return _


def request_schema(name: str, schema: Type[JsonSchemaMixin] = None, schema_file: str = None,
                   title="", description=""):
    """
    1. request schema can help render swagger schema file
    2. validate request data by schema
    3. if schema_file is not None, then load schema from schema_file
    4. inject validated data to method by name

    :param name: inject name to method
    :param schema: schema type
    :param schema_file: the file container schema json schema
    :param title: schema title
    :param description: schema description
    """

    if not schema and not schema_file:
        raise ValueError("schema or schema_file must be not None")

    def _(func):
        # helper render swagger schema
        func_name = func.__name__
        if func_name == 'get':
            _schema = getattr(func, '__path_schema__', {})
            _schema["default"] = {"schema": schema, "schema_file": schema_file, "description": description,
                                  "title": title, "content": "application/json"}
            setattr(func, '__path_schema__', _schema)
        else:
            _schema = getattr(func, '__request_schema__', {})
            _schema["default"] = {"schema": schema, "schema_file": schema_file, "description": description,
                                  "title": title, "content": "application/json"}
            setattr(func, '__request_schema__', _schema)

        def get_json_data(self: Handler) -> (bool, Any):
            if func_name == 'get':
                text = self.get_argument('data', '')
                if not text:
                    text = "{}"
            else:
                text = self.request.body

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
                        logger.exception("request body is invalid json data", text)
                    return False, None

            return True, json_data

        async def validate_request_with_schema_class(self: Handler, *args, **kwargs):
            ok, json_data = get_json_data(self)
            if not ok:
                self.write(Result.failre("request body is invalid json data"))
                return

            try:
                kwargs[name] = schema.from_dict(json_data)
            except dataclasses_jsonschema.ValidationError as e:
                if logging.DEBUG >= logging.root.level:
                    logger.exception(
                        "request schema validation error, json_data is %s, schema is %s", json_data, schema)
                self.write(Result.error(e))
                return

            result = await func(self, *args, **kwargs)
            if isinstance(result, JsonSchemaMixin):
                return result

        async def validate_request_with_schema_file(self: Handler, *args, **kwargs):
            ok, json_data = get_json_data(self)
            if not ok:
                self.write(Result.failre("request body is invalid json data"))

            schema_validate = get_schema_validate(schema_file)
            try:
                schema_validate(json_data)
            except JsonSchemaException as e:
                if logging.DEBUG >= logging.root.level:
                    logger.exception(
                        "request schema validation error, json_data is %s, schema is %s", json_data, schema_file)
                self.write(Result(code=-2, msg=e.message))
                return

            kwargs[name] = json_data
            result = await func(self, *args, **kwargs)
            if isinstance(result, JsonSchemaMixin):
                return result

        if schema_file:
            functools.wraps(func)(validate_request_with_schema_file)
            return validate_request_with_schema_file
        else:
            functools.wraps(func)(validate_request_with_schema_class)
            return validate_request_with_schema_class

    return _

# def path_schema(schema: Type[JsonSchemaMixin], title="", description=""):
#     def _(func):
#         _schema = getattr(func, '__path_schema__', {})
#         _schema["default"] = {"schema": schema, "description": description, "title": title}
#         setattr(func, '__path_schema__', _schema)
#         return func
#
#     return _
