from dataclasses import dataclass, field

from dataclasses_jsonschema import JsonSchemaMixin


@dataclass
class SQLRequestSchema(JsonSchemaMixin):
    """SQLRequestSchema"""
    sql: str = field(metadata={"description": "the jinja template for the sql query"})
    # override: bool = field(default=False, metadata={"description": "override existing sql"})
    mode: str = field(default="execute", metadata={"description": "must be execute or paginate"})
