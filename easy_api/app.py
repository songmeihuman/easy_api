import logging

import tornado.ioloop
import tornado.log
import tornado.options
import tornado.web
import uvloop
from tornado.options import define, options

from easy_api import application, celery, configs, celery_waiter
from easy_api.schema import swagger

define("config", default="./config.yaml", help="config file path")


def start_app():
    tornado.options.parse_command_line()
    config_path = options.config

    logger = logging.getLogger("easy_api.__main__")

    uvloop.install()
    configs.install(config_path)
    application.install()
    celery.install()
    handlers = application.get_handlers()
    app = tornado.web.Application(handlers)
    celery_waiter.install()

    if logging.DEBUG >= logging.root.level:
        for handler in handlers:
            logger.debug("loaded handler [%s] %s", handler[0], handler[1])

    server = configs.server
    if configs.swagger.enable:
        swagger.install(app, handlers)
        logger.info("Doc started at http://%s:%s%s", server.host, server.port, configs.swagger.path)

    app.listen(server.port, server.host)
    logger.info("Server started at http://%s:%s", server.host, server.port)

    # loop = asyncio.get_event_loop()
    # loop.set_debug(True)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    start_app()
