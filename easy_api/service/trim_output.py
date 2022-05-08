import ast
from ast import Call, Attribute, Name, Num, Str
from typing import Any, Union, List, Dict

import jinja2

_types = {
    'int': int,
    'str': str,
    'float': float,
    'bool': bool
}


def v_func(args: List[Name], data: Dict, context):
    """从字典中取值"""
    result = data.get(args[0].id) if data else None
    if result is None:
        result = context.get(args[0].id, None)
    return result


def t_func(args: List[Name], data, context):
    """ 类型转换 """
    type_name = args[0].id

    if isinstance(data, list):
        return [_types[type_name](x) for x in data]
    else:
        return _types[type_name](data)


def n_func(args: List[Name], data, context):
    """ 增加命名 """
    return {args[0].id: data}


def r_func(args: List[Str], data, context):
    """ 模板 """
    template = jinja2.Template(args[0].s)
    return template.render(**context, **data)


def k_func(args: List[Name], data, context):
    """ 从列表中取出一组数据 """
    key = args[0].id
    return [x[key] for x in data if key in x]


def g_func(args: List[Num], data, context):
    """ 从列表中取值，按下标 """
    return data[args[0].n]


def s_func(args: List[Num], data, context):
    """ 从列表中取值，类切片 """
    return data[args[0].n:args[1].n]


_func = {
    'v': v_func,
    't': t_func,
    'n': n_func,
    'r': r_func,
    'k': k_func,
    'g': g_func,
    's': s_func,
}


class WalkAST(ast.NodeVisitor):
    data = None
    context = None

    def __init__(self, data, context):
        self.context = context
        self.data = data

    def visit_Call(self, node: Call) -> Any:
        func_name = None
        if isinstance(node.func, Name):
            func_name = node.func.id
        elif isinstance(node.func, Attribute):
            func_name = node.func.attr

        if not func_name:
            return

        # 递归执行，先处理最底层的
        ast.NodeVisitor.generic_visit(self, node)
        # 然后再来执行这次的
        self.data = _func[func_name](node.args, self.data, self.context)


def process(data: Union[dict, list, tuple], rules: dict, context: dict):
    """
    process data with rules
    :param data: the data to process
    :param rules:
    :param context:
    :return:
    """
    result = {}
    for name, rule in rules.items():
        tree = ast.parse(rule, mode='eval')
        w = WalkAST(data, context)
        w.visit(tree)
        result[name] = w.data

    return result
