import asyncio
import os
import shutil

import aiomysql
import aiosqlite
import pytest

from easy_api import configs
from easy_api.service import db

DB_NAME = "easy_api_test"
database_items = [
    ("John", 25),
    ("Wick", 25),
    ("Mary", 30),
    ("Peter", 27),
]


@pytest.fixture(scope='function')
def tmp_dst():
    dst_dir = 'test_files_dst'
    full_dst_dir_path = os.path.join(configs.project_root, dst_dir)
    try:
        yield dst_dir
    finally:
        if os.path.exists(full_dst_dir_path):
            shutil.rmtree(full_dst_dir_path)


async def create_test_table_in_mysql(datas):
    db_config = db.find_config("mysql")
    conn = await aiomysql.connect(host=db_config.host, port=db_config.port, db=db_config.db,
                                  user=db_config.user, password=db_config.password)

    create_table_sql = f"""
    CREATE TABLE {DB_NAME} (name VARCHAR(255), age INTEGER, PRIMARY KEY (name));
    """
    cur = await conn.cursor()
    await cur.execute(f"DROP TABLE IF EXISTS {DB_NAME}")
    await cur.execute(create_table_sql)
    await cur.executemany(f"INSERT INTO {DB_NAME} (name, age) VALUES (%s, %s)", datas)
    await conn.commit()
    await cur.close()
    return conn


async def create_test_table_in_sqlite(datas):
    db_config = db.find_config("sqlite")
    sql = f"""CREATE TABLE {DB_NAME} (name text, age real)"""
    conn = await aiosqlite.connect(db_config.db)
    await conn.execute(sql)
    await conn.executemany(f"INSERT INTO {DB_NAME} (name, age) VALUES (?, ?)", datas)
    await conn.commit()
    return conn


async def drop_test_table_in_mysql(conn):
    cur = await conn.cursor()
    await cur.execute(f"DROP TABLE {DB_NAME}")
    await cur.close()
    conn.close()


async def drop_test_table_in_sqlite(db):
    await db.execute(f"DROP TABLE {DB_NAME}")
    await db.close()


@pytest.fixture
def setup_mysql():
    loop = asyncio.get_event_loop()
    aiomysql_db = loop.run_until_complete(create_test_table_in_mysql(database_items))
    try:
        yield
    finally:
        loop.run_until_complete(drop_test_table_in_mysql(aiomysql_db))


@pytest.fixture
def setup_sqlite():
    loop = asyncio.get_event_loop()
    sqlite_db = loop.run_until_complete(create_test_table_in_sqlite(database_items))
    try:
        yield
    finally:
        loop.run_until_complete(drop_test_table_in_sqlite(sqlite_db))


@pytest.fixture(scope="module", autouse=True)
def clean_sqlite_file():
    yield
    if os.path.isfile('sqlite.db'):
        os.remove('sqlite.db')
