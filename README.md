# Easy API

EasyAPI 是一个非常简单编写接口的工具：

1. SQL 即接口
2. 支持 **jinja** 模板引擎，可以识别引擎的变量作为接口的入参
3. 每一个接口都会生成项目文件，可以手动修改生成后文件，满足个性化需求
4. 自动生成 **openapi** 文档，附带有一个 UI 界面
5. 支持非 SQL 接口，即自己写 Python 接口，会被当作一个任务在 celery 里面执行并返回结果
6. 支持类似 linux 管道处理，SQL 接口生成的数据输入到 Python 接口里面二次加工
7. 不管是 SQL 接口，Python接口，管道操作都是异步非阻塞

## 安装

本项目只支持 Pyhton3

- 下载项目到本地

```bash
git clone https://github.com/songmeihuman/easy_api.git
```

- 进入项目目录

```bash
cd easy_api
```

- 新建一个 Python 虚拟环境

```bash
python3 -m venv venv
```

- 安装依赖

```bash
./venv/bin/python -m pip install -r requirements.txt
```

- 新建配置

位置可以随意指定，这里演示放在项目根目录下

```bash
cp config.yaml.example config.yaml
```

- 可选：启动 Worker

如果你有 Python 接口，就需要启动，否则调用 Python 接口会卡住并且无法得到结果

```bash
./venv/bin/python -m celery -A easy_api worker -l info
```

如果配置不在根目录，需要手动指定

```bash
./venv/bin/python -m celery -A easy_api worker -l info --config <your-config-path>
```

- 启动

```bash
./venv/bin/python main.py
```

如果配置不在根目录，需要手动指定

```bash
./venv/bin/python main.py --config <your-config-path>
```

## 使用

### 新建包

```bash
# 新建一个叫 demo 的包，调用完后会自动生成 easy_api/demo 这个目录，是一个真实的 Python package
curl -X 'POST' \
  'http://localhost:8000/easy_api/package/demo' \
  -H 'accept: application/json' \
  -d ''
```

### SQL 接口

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

### Python 接口

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
**service/hello.py** 里面的 **run** 方法是接口的代码逻辑，默认定义了一个方法参数: name

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

### 管道

同时调用 SQL 接口和 Python 接口

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
      "output": {"sql_result": "v(result).v(result)"},
      "layer": 0
    },
    {
      "package_name": "demo",
      "name": "hello",
      "kwargs": {"name": "Duo"},
      "output": {"task_result": "v(result)"},
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