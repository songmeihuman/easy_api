from dataclasses import dataclass, field

from dataclasses_jsonschema import JsonSchemaMixin


@dataclass
class SQLRequestSchema(JsonSchemaMixin):
    """SQLRequestSchema"""
    sql: str = field(metadata={"description": "the jinja template for the sql query"})
    count_sql: str = field(
        default="",
        metadata={"description": "the jinja template for the sql query to count the number of rows, "
                                 "it enables from paging mode. If not provided, "
                                 "the content will automat generate from sql"})
    mode: str = field(default="execute", metadata={"description": "must be execute or paging"})
    database: str = field(default="default", metadata={"description": "the database to use"})
    export_xlsx: bool = field(default=False, metadata={"description": "support export to xlsx"})
