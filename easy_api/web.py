import logging
from abc import ABC
from dataclasses import asdict
from typing import Union

import orjson
import tornado.web
from dataclasses_jsonschema import JsonSchemaMixin
from tornado.escape import utf8
from tornado.util import unicode_type

logger = logging.getLogger("easy_api.web")


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
