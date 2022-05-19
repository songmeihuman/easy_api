# 使用

## 新建包

```bash
# 新建一个叫 demo 的包，调用完后会自动生成 easy_api/demo 这个目录，是一个真实的 Python package
curl -X 'POST' \
  'http://localhost:8000/easy_api/package/demo' \
  -H 'accept: application/json' \
  -d ''
```

## SQL 接口

- 新建 SQL 接口

```bash
# 在 demo 包下新建了一个名叫 test 的 SQL 接口，SQL 是 select * from company
curl -X 'PUT' \
  'http://localhost:8000/easy_api/package/demo/sql/test' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "sql": "select * from company",
  "mode": "execute"
}'
```

- 调用 SQL 接口

```bash
# 调用位于 demo 包下的 test 接口
curl -X 'POST' \
  'http://localhost:8000/demo/test' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{}'

# 返回：
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "ID": 1,
      "NAME": "Duo",
      "AGE": 30,
      "ADDRESS": "London",
      "SALARY": 65000
    }
  ],
  "changes": 0
}
```

## Python 接口

- 新建 Python 接口

```bash
# 在 demo 包下新建了一个名叫 hello 的 Python 接口
curl -X 'POST' \
  'http://localhost:8000/easy_api/package/demo/task/hello' \
  -H 'accept: application/json' \
  -d ''
```

- 增加业务代码逻辑

通过第一步生成了下面几个文件：

easy_api/demo/handle/hello.py  
easy_api/demo/handle/schema/hello.py  
easy_api/demo/service/hello.py

**schema/hello.py** 里面的 **HelloSchem** 类定义了接口的入参，默认定义了一个 name 自动  
**service/hello.py** 里面的 **run** 方法是接口的代码逻辑，默认定义了一个参数: name，特别说明 service 里面 run 方法，必须接收其他不相关的参数，可以按下面例子用 **__ 放弃处理。

```python
# server/hello.py 文件里面主要的代码
def run(name: str, **__) -> str:
    """ run hello
    """
    return f"hello {name}"
```

- 调用 Python 接口

```bash
curl -X 'POST' \
  'http://localhost:8000/demo/hello' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Duo"
}'

# 返回：
{
  "code": 0,
  "msg": "",
  "data": "hello Duo"
}
```

## 管道

- 例子：同时调用 SQL 接口和 Python 接口

```bash
curl -X 'POST' \
  'http://localhost:8000/easy_api/pipeline' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "tasks": [
    {
      "package_name": "demo",
      "name": "test",
      "kwargs": {},
      "output": {"sql_result": "{{ result.data }}"},
      "layer": 0
    },
    {
      "package_name": "demo",
      "name": "hello",
      "kwargs": {"name": "Duo"},
      "output": {"task_result": "{{ result.data }}"},
      "layer": 0
    }
  ]
}'

# 返回
{
  "code": 0,
  "msg": "",
  "data": {
    "sql_result": [
      {
        "ID": 1,
        "NAME": "Duo",
        "AGE": 30,
        "ADDRESS": "London",
        "SALARY": 65000
      }
    ],
    "task_result": "hello Duo"
  }
}
```

- 例子：上一个任务的输出作为下一个任务的输入。

layer 为 0 的任务先执行，在 kwargs 找到了输入 {"name": "Duo"}，执行后输出 {"result": "hello Duo"}，经过 output 的修改变成 {"name": "hello Duo"}。  
layer 为 1 的任务执行，从上一个任务的结果找到 name 作为输入，得到结果 {"result": "hello hello Duo"}，经过 output 的修改变成 {"task_result": "hello hello
Duo"}。

```bash
curl -X 'POST' \
  'http://localhost:8000/easy_api/pipeline' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "tasks": [
    {
      "package_name": "demo"  ,
      "name": "hello",
      "kwargs": {"name": "Duo"},
      "output": {"name": "{{ result.data }}"},
      "layer": 0
    },
    {
      "package_name": "demo",
      "name": "hello",
      "kwargs": {},
      "output": {"task_result": "{{ result.data }}"},
      "layer": 1
    }
  ]
}'

# 返回
{
  "code": 0,
  "msg": "",
  "data": {
    "task_result": "hello hello Duo"
  }
}
```

- 例子：多个任务的输出作为下一个任务的输入。

已有 Python 接口 echo：

```python
def run(num: int, **__) -> int:
    """ run echo
    """
    return num
```

已有 Python 接口 sum：

```python
def run(val1: int, val2: int, **__) -> int:
    """ run sum
    """
    return val1 + val2
```

执行：

两个 layer 为 0 的任务 echo 先执行，然后将结果作为输入执行 layer 为 1 的任务 sum。

```bash
curl -X 'POST' \
  'http://localhost:8000/easy_api/pipeline' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "tasks": [
    {
      "package_name": "demo"  ,
      "name": "echo",
      "kwargs": {"num": 42},
      "output": {"val1": "{{ result.data }}"},
      "layer": 0
    },
    {
      "package_name": "demo"  ,
      "name": "echo",
      "kwargs": {"num": 42},
      "output": {"val2": "{{ result.data }}"},
      "layer": 0
    },
    {
      "package_name": "demo",
      "name": "sum",
      "kwargs": {},
      "output": {"task_result": "{{ result.data }}"},
      "layer": 1
    }
  ]
}'

# 返回
{
  "code": 0,
  "msg": "",
  "data": {
    "task_result": 84
  }
}
```