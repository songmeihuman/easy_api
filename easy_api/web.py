import functools
import logging
from abc import ABC
from dataclasses import dataclass, asdict, field
from typing import Union, Type

import dataclasses_jsonschema
import orjson
import tornado.web
from dataclasses_jsonschema import JsonSchemaMixin
from fastjsonschema import JsonSchemaException
from tornado.escape import utf8
from tornado.util import unicode_type

from easy_api.schema import get_schema_validate

logger = logging.getLogger("easy_api.web")


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
        async def inner_response_schema(self, *args, **kwargs):
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
        _schema = getattr(func, '__request_schema__', {})
        _schema["default"] = {"schema": schema, "schema_file": schema_file, "description": description,
                              "title": title, "content": "application/json"}
        setattr(func, '__request_schema__', _schema)

        async def validate_request_with_schema_class(self, *args, **kwargs):
            try:
                json_data = orjson.loads(self.request.body)
            except ValueError:
                try:
                    json_data = orjson.loads(
                        self.request.body.replace(b'\\\\', b'\\')
                    )
                except ValueError:
                    if logging.DEBUG >= logging.root.level:
                        logger.exception(
                            "request body is invalid json data", self.request.body)
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

        async def validate_request_with_schema_file(self, *args, **kwargs):
            try:
                json_data = orjson.loads(self.request.body)
            except ValueError:
                self.write(Result.failre("request body is invalid json data"))
                return

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


class Handler(tornado.web.RequestHandler, ABC):

    def write(self, chunk: Union[str, bytes, dict, JsonSchemaMixin]) -> None:
        if self._finished:
            raise RuntimeError("Cannot write() after finish()")
        if isinstance(chunk, JsonSchemaMixin):
            chunk = asdict(chunk)
        if isinstance(chunk, dict):
            chunk = orjson.dumps(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self._write_buffer.append(chunk)
            return
        if not isinstance(chunk, (bytes, unicode_type, dict)):
            message = "write() only accepts bytes, unicode, and dict objects"
            if isinstance(chunk, list):
                message += (
                        ". Lists not accepted for security reasons; see "
                        + "http://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.write"  # noqa: E501
                )
            raise TypeError(message)
        chunk = utf8(chunk)
        self._write_buffer.append(chunk)
