from dataclasses import dataclass, field
from typing import Union

from dataclasses_jsonschema import JsonSchemaMixin


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
class PagingResult(JsonSchemaMixin):
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
