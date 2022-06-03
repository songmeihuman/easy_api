import urllib.parse
from enum import IntEnum
from io import BytesIO

import xlsxwriter
from tornado.web import RequestHandler

from easy_api.schema import Result


class ExportType(IntEnum):
    XLSX = 1


async def export_xlsx(handler: RequestHandler, data: list, file_name: str = "export", header: str = None) -> None:
    if not header:
        header = ",".join(data[0].keys())

    header_dict = {}
    for h in header.split(","):
        hs = h.split(':')
        header_dict[hs[0]] = hs[-1]

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # write header
    worksheet.write_row(0, 0, header_dict.values())

    # write data
    for i, item in enumerate(data):
        text = [
            '%s' % item.get(x, "") for x in header_dict
        ]
        worksheet.write_row(i + 1, 0, text)

    workbook.close()

    file_name = urllib.parse.quote(file_name)

    handler.set_header('Content-Type', "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    handler.set_header("Content-Disposition", f"attachment; filename={file_name}.xlsx")

    output.seek(0)
    handler.write(output.read())
    await handler.finish()


async def run(export_type: ExportType, handler: RequestHandler, data: list, file_name: str = "export",
              header: str = None, **__) -> Result:
    """
    Exports data to a CSV file.

    :param export_type: export type.
    :param handler: tornado web RequestHandler.
    :param data: The data to be exported.
    :param file_name: The name of the file to be exported.
    :param header: The header of the CSV file.
    :return: None
    """
    if export_type == ExportType.XLSX:
        await export_xlsx(handler, data, file_name, header)
        return Result.success("ok")

    return Result.failre("not implementation")
