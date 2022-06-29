import functools
import logging
from dataclasses import dataclass, field
from io import BytesIO
from typing import Type, Callable, NewType
from openpyxl import load_workbook

from dataclasses_jsonschema import JsonSchemaMixin, FieldEncoder

from easy_api.web import Handler
from .entity import Result
from .spec import ResponseSchemaSpec, RequestBodyJsonFileSpec, RequestBodySchemaSpec, ParameterSchemaSpec, \
    ParameterJsonFileSpec
from .utils import safe_load_json
from ..service.data_file import get_datas_from_file

log = logging.getLogger(__name__)


def apply_spec_to_api(func: Callable, spec):
    specs = getattr(func, '__easy_specs__', [])
    specs.append(spec)
    setattr(func, '__easy_specs__', specs)


def response_schema(schema: Type[JsonSchemaMixin] = None, status_code=200, content_type="application/json"):
    """
    1. response schema can helper render swagger schema file
    2. auto write json response from method return value
    :param schema: the schema class
    :param status_code: the status code for response, default is 200
    :param content_type: the content type for response, default is application/json
    :return:
    """

    def _(func):
        spec = ResponseSchemaSpec(schema, status_code=status_code, content_type=content_type)
        apply_spec_to_api(func, spec)

        @functools.wraps(func)
        async def inner_response_schema(self: Handler, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            if isinstance(result, schema):
                self.write(result)

        return inner_response_schema

    return _


def request_schema(name: str, schema: Type[JsonSchemaMixin] = None, schema_file: str = None):
    """
    1. request schema can help render swagger schema file
    2. validate request data by schema
    3. if schema_file is not None, then load schema from schema_file
    4. inject validated data to method by name

    :param name: inject name to method
    :param schema: schema type
    :param schema_file: the file container schema json schema
    """

    if not schema and not schema_file:
        raise ValueError("schema or schema_file must be not None")

    def _(func):
        content_type = "application/json"

        if schema_file:
            spec = RequestBodyJsonFileSpec(name, schema_file, content_type=content_type)
        else:
            spec = RequestBodySchemaSpec(name, schema, content_type=content_type)

        apply_spec_to_api(func, spec)

        @functools.wraps(func)
        async def request_schema_inner(self: Handler, *args, **kwargs):
            ok, json_data = safe_load_json(self.request.body)
            if not ok:
                self.write(Result.failre("request body is invalid json data"))
                return

            error_msg, result = await spec.validate(json_data)
            if error_msg:
                self.write(Result.failre(error_msg))
                return

            kwargs[name] = result
            result = await func(self, *args, **kwargs)
            if isinstance(result, JsonSchemaMixin):
                return result

        return request_schema_inner

    return _


def header_schema(name: str, schema: Type[JsonSchemaMixin] = None, schema_file: str = None):
    if not schema and not schema_file:
        raise ValueError("schema or schema_file must be not None")

    def _(func):
        if schema_file:
            spec = ParameterJsonFileSpec(name, schema_file, parameter_type="header")
        else:
            spec = ParameterSchemaSpec(name, schema, parameter_type="header")

        apply_spec_to_api(func, spec)

        @functools.wraps(func)
        async def parameters_schema_inner(self: Handler, *args, **kwargs):
            json_text = self.request.headers.get('Datas')
            if not json_text:
                return

            json_data = safe_load_json(json_text)
            error_msg, result = await spec.validate(json_data)
            if error_msg:
                self.write(Result.failre(error_msg))
                return

            kwargs[name] = result
            result = await func(self, *args, **kwargs)
            if isinstance(result, JsonSchemaMixin):
                return result

        return parameters_schema_inner

    return _


def query_schema(name: str, schema: Type[JsonSchemaMixin] = None, schema_file: str = None):
    if not schema and not schema_file:
        raise ValueError("schema or schema_file must be not None")

    def _(func):
        if schema_file:
            spec = ParameterJsonFileSpec(name, schema_file, parameter_type="query")
        else:
            spec = ParameterSchemaSpec(name, schema, parameter_type="query")

        apply_spec_to_api(func, spec)

        @functools.wraps(func)
        async def parameters_schema_inner(self: Handler, *args, **kwargs):
            json_text = self.get_argument('datas', None)
            if not json_text:
                return

            json_data = safe_load_json(json_text)
            error_msg, result = await spec.validate(json_data)
            if error_msg:
                self.write(Result.failre(error_msg))
                return

            kwargs[name] = result
            result = await func(self, *args, **kwargs)
            if isinstance(result, JsonSchemaMixin):
                return result

        return parameters_schema_inner

    return _


Uploader = NewType('Uploader', str)


class UploaderField(FieldEncoder):

    @property
    def json_schema(self):
        return {'type': 'string', 'format': 'binary'}


JsonSchemaMixin.register_field_encoders({Uploader: UploaderField()})


@dataclass
class BatchUploadSchema(JsonSchemaMixin):
    """ list_datas schema """
    upload_file: Uploader = field(metadata={"description": "batch upload datas by xlsx file"})
    fields: str = field(metadata={
        "description": "the relationship between header of upload file and database field name",
    }, default="field1:title1,field2:title2")


def batch_upload_schema(name: str):

    def _(func):
        spec = RequestBodySchemaSpec(name, BatchUploadSchema, content_type="multipart/form-data")
        apply_spec_to_api(func, spec)

        @functools.wraps(func)
        async def batch_upload_schema_inner(self: Handler, *args, **kwargs):
            upload_file = self.request.files["upload_file"][0]
            values = get_datas_from_file(upload_file["filename"], upload_file["body"])
            kwargs[name] = values
            return await func(self, *args, **kwargs)

        return batch_upload_schema_inner

    return _
