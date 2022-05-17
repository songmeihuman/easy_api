# Easy API

EasyAPI 是一个非常简单编写接口的工具：

1. SQL 即接口
2. 支持 **jinja** 模板引擎，可以识别引擎的变量作为接口的入参
3. 每一个接口都会生成项目文件，可以手动修改生成后文件，满足个性化需求
4. 自动生成 **openapi** 文档，附带有一个 UI 界面
5. 支持非 SQL 接口，即自己写 Python 接口，会被当作一个任务在 [celery](https://github.com/celery/celery) 里面执行并返回结果
6. 支持类似 linux 管道，例如：SQL 接口生成的数据输入到 Python 接口里面二次加工
7. 不管是 SQL 接口，Python接口，管道操作都是异步非阻塞

## 安装

本项目只支持 Python3

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

配置文件可以放在其他地方，这里演示放在项目根目录下

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

- 启动项目
```bash
./venv/bin/python main.py
```

如果配置不在根目录，需要手动指定

```bash
./venv/bin/python main.py --config <your-config-path>
```

## 快速开始

- 新建包

新建完后，需要在配置中启用它并且重启项目才会生效，见 [配置](#配置)

```bash
# 新建一个叫 demo 的包，调用完后会自动生成 easy_api/demo 这个目录，是一个真实的 Python package
curl -X 'POST' \
  'http://localhost:8000/easy_api/package/demo' \
  -H 'accept: application/json' \
  -d ''
```

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

- 其他 Python 接口、管道 接口请查看[使用文档](docs/usage.md#python-接口)

## 配置

- server

apps 是一个列表，里面是需要启用的包名字。  
easy_api 是开发时候依赖项，正式使用不需要可以删掉，但是 easy_api 这个文件夹不能删除。

```yaml
server:
  # 监听主机和端口
  host: "localhost"
  port: 8000
  # 时区
  timezone: 'Asia/Shanghai'
  # 启用的包
  apps:
    - easy_api
```

- database

定义了多数据源，支持 sqlite，mysql，mariadb，对应 type 字段。  
一个 SQL 规则支持绑定一个数据源，匹配 name 字段。

```yaml
database:
  instances:
    - name: "default"
      type: "sqlite"
      db: "sqlite.db"
    - name: "mysql-example"
      type: "mysql"
      db: "mysql"
      host: "localhost"
      port: 3306
      user: "root"
      password: "root"
      charset: "utf8mb4"
```

- celery

如果使用 Python 接口，就必须设置 celery 配置项。  
celery 本身不是异步的，为了支持任务异步得到结果，所以 **backend 只能用 redis**

```yaml
celery:
  broker: 'redis://localhost:6379/0'
  backend: 'redis://localhost:6379/0'
  serializer: 'msgpack'
  timezone: 'Asia/Shanghai'
```