import aiomysql
import aiosqlite
from pymysql import FIELD_TYPE, converters
from typing_extensions import TypedDict

from easy_api import configs
from easy_api.configs import DatabaseCell

# avoid converting mysql date to datetime
mysql_conv = {
    **converters.conversions,
    FIELD_TYPE.DATETIME: str,
    FIELD_TYPE.DATE: str,
    FIELD_TYPE.TIMESTAMP: str,
}


class DatabaseResult(TypedDict):
    """
    Result of query
    """
    result: list
    changes: int


def find_config(db_alias: str) -> DatabaseCell:
    """
    Find the configuration of the database with the given alias.

    :param db_alias: The alias of the database to find.
    :return: The configuration of the database with the given alias.
    """
    found = next((x for x in configs.database.instances if x.name == db_alias), None)
    return found


async def execute_mysql(db_config: DatabaseCell, sql: str, bind_params: list,
                        autocommit: bool = True) -> DatabaseResult:
    """
    Execute a SQL statement in mysql and return the result.

    :param db_config: The configuration of the database to use.
    :param sql: The SQL statement to execute.
    :param bind_params: A dictionary of parameters to bind to the SQL statement.
    :param autocommit: Whether to automatically commit the transaction.
    :return: The result of the SQL statement.
    """
    pool = await aiomysql.create_pool(host=db_config.host, port=db_config.port, db=db_config.db,
                                      user=db_config.user, password=db_config.password, conv=mysql_conv,
                                      cursorclass=aiomysql.cursors.DictCursor)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # FIXME this is aiomysql bug, it doesn't support named parameters
            query = sql.replace('%', '%%').replace('?', '%s')
            changes = await cur.execute(query, bind_params)
            if autocommit:
                await conn.commit()
            result = await cur.fetchall()

    pool.close()
    return {'result': result, 'changes': changes}


async def execute_sqlite(db_config: DatabaseCell, sql: str, bind_params: list,
                         autocommit: bool = True) -> DatabaseResult:
    """
    Execute a SQL statement in sqlite and return the result.

    :param db_config: The configuration of the database to use.
    :param sql: The SQL statement to execute.
    :param bind_params: A dictionary of parameters to bind to the SQL statement.
    :param autocommit: Whether to automatically commit the transaction.
    :return: The result of the SQL statement.
    """
    async with aiosqlite.connect(db_config.db) as db:
        db.row_factory = aiosqlite.Row
        async with await db.execute(sql, bind_params) as cur:
            if autocommit:
                await db.commit()
            result = await cur.fetchall()
            changes = db.total_changes

    return {'result': [dict(x) for x in result], 'changes': changes}


async def execute(db_alias: str, sql: str, bind_params: list = None, autocommit: bool = True) -> DatabaseResult:
    """
    Execute a SQL statement and return the result.
    If it can't find the db alias in config, raise an exception.

    :param db_alias: The alias of the database to use.
    :param sql: The SQL statement to execute.
    :param bind_params: A dictionary of parameters to bind to the SQL statement.
    :param autocommit: Whether to automatically commit the transaction. default: True
    :return: The result of the SQL statement.
    """
    db_config = find_config(db_alias)
    if db_config is None:
        raise ValueError(f"Database alias '{db_alias}' not found.")

    if db_config.type == 'mysql':
        return await execute_mysql(db_config, sql, bind_params, autocommit)
    elif db_config.type == 'sqlite':
        return await execute_sqlite(db_config, sql, bind_params, autocommit)
    else:
        raise ValueError(f"Database type '{db_config.type}' not supported.")
