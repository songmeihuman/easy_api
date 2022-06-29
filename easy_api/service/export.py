import urllib.parse

from tornado.web import RequestHandler

from easy_api.service.data_file import get_xlsx_from_datas


class HandlerWrite:
    _handler: RequestHandler = None

    def __init__(self, handler):
        self._handler = handler

    def write(self, chunk) -> int:
        self._handler.write(chunk)
        return len(chunk)

    def flush(self):
        self._handler.flush()


async def export_xlsx_file(handler: RequestHandler, data: list, file_name: str = "export", header: str = None) -> None:
    # file name
    file_name = urllib.parse.quote(file_name)
    handler.set_header('Content-Type', "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    handler.set_header("Content-Disposition", f"attachment; filename={file_name}.xlsx")

    handler_write = HandlerWrite(handler)
    get_xlsx_from_datas(handler_write, data, header)
    await handler.finish()
