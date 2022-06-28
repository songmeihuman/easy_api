from unittest import TestCase

import pytest

from easy_api.service import db

DB_NAME = "easy_api_test"

RULES = [
    (
        f"select name, age from {DB_NAME} where age > ?", [27],
        "result", [{"name": "Mary", "age": 30}]
    ),
    (
        f"select name from {DB_NAME} where name like ?", ["%et%"],
        "result", [{"name": "Peter"}]
    ),
    (
        f"select name, age from {DB_NAME} order by age desc limit ?", [1],
        "result", [{"name": "Mary", "age": 30}]
    ),
    (
        f"select name, age from {DB_NAME} order by age desc limit ? offset ?", [1, 1],
        "result", [{"name": "Peter", "age": 27}]
    ),
    (
        f"insert into {DB_NAME} (name, age) values (?, ?)", ["Tom", 28],
        "changes", 1
    ),
    (
        f"update {DB_NAME} set age = ? where name = ?", [29, "Tom"],
        "changes", 0
    ),
    (
        f"update {DB_NAME} set age = ? where name = ?", [31, "Mary"],
        "changes", 1
    ),
    (
        f"delete from {DB_NAME} where name = ?", ["John"],
        "changes", 1
    ),
    (
        f"delete from {DB_NAME} where age = ?", [25],
        "changes", 2
    )
]


@pytest.mark.usefixtures("setup_mysql")
@pytest.mark.parametrize(["query", "bind_params", "expected_field", "expected"], RULES)
async def test_basic_mysql(query, bind_params, expected_field, expected):
    result = await db.execute("mysql", query, bind_params)
    if expected_field == "result":
        TestCase().assertListEqual(result["result"], expected)
    elif expected_field == "changes":
        assert result["changes"] == expected
    else:
        assert False


@pytest.mark.usefixtures("setup_sqlite")
@pytest.mark.parametrize(["query", "bind_params", "expected_field", "expected"], RULES)
async def test_basic_sqlite(query, bind_params, expected_field, expected):
    result = await db.execute("sqlite", query, bind_params)
    if expected_field == "result":
        TestCase().assertListEqual(result["result"], expected)
    elif expected_field == "changes":
        assert result["changes"] == expected
    else:
        assert False


@pytest.mark.usefixtures("setup_mysql")
async def test_mysql_datetime():
    query = f"select now() as now"
    result = await db.execute("mysql", query)
    assert isinstance(result["result"][0]["now"], str)
