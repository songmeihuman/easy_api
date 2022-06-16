from dataclasses import dataclass, field
from typing import Union

from dataclasses_jsonschema import JsonSchemaMixin


@dataclass
class SQLRequestSchema(JsonSchemaMixin):
    """SQLRequestSchema"""
    sql: str = field(metadata={"description": "the jinja template for the sql query"})
    database: str = field(default="default", metadata={"description": "the database to use"})
    method: str = field(default="post", metadata={"description": "get or post"})
    count_sql: Union[bool, str] = field(
        default=False,
        metadata={"description": "the jinja template for the sql query to count the number of rows, "
                                 "if provided true, the content will automate generate from sql, "
                                 "or content from provided string, default is false."})
    export_xlsx: Union[bool, str] = field(
        default=False,
        metadata={"description": "support export to xlsx"})
