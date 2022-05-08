import pytest

from easy_api.service import trim_output


@pytest.mark.parametrize(["output", "rule", "context", "expect", "message"], (
        ({"name": "Duo", "age": 16}, {"name": "v(name)"}, {}, {"name": "Duo"}, "normal"),
        ({"name": "Duo", "age": 16}, {"sex": "v(sex)"}, {"sex": 1}, {"sex": 1}, "get value from context"),
        ({"name": "Duo", "age": 16}, {"age": "v(age).t(str)"}, {}, {"age": "16"}, "get value and then to be string"),
        ({"name": "Duo", "age": 16}, {"age": "v(age).n(int)"}, {}, {"age": {"int": 16}},
         "get value and then to be dict"),
        ({"name": "Duo", "age": 16}, {"answer": """r("I am {{name}}")"""}, {}, {"answer": "I am Duo"},
         "jinja template"),
        ({"name": "Duo", "age": 16}, {"answer": """r("I am {{newname}}")"""}, {"newname": "Lisa"},
         {"answer": "I am Lisa"}, "jinja template with context"),
        ([{"value": 4}, {"value": 2}], {"answer": "k(value)"}, {}, {"answer": [4, 2]}, "get values from list"),
        ([{"value": 4}, {"value": 2}], {"answer": "g(1)"}, {}, {"answer": {"value": 2}},
         "get value by index from list"),
        ([{"value": 4}, {"value": 2}], {"answer": "s(0, 1)"}, {}, {"answer": [{"value": 4}]},
         "slice list"),
        ([{"value": 4}, {"value": 2}], {"answer": "s(0, 1).k(value)"}, {}, {"answer": [4]},
         "slice list and them to be list"),
))
def test_trim_output(output, rule, context, expect, message):
    output = trim_output.process(output, rule, context)
    assert output == expect, message
