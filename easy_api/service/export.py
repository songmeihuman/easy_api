import urllib.parse
from io import BytesIO

import xlsxwriter
from tornado.web import RequestHandler


async def export_xlsx_file(handler: RequestHandler, data: list, file_name: str = "export", header: str = None) -> None:
    # file name
    file_name = urllib.parse.quote(file_name)
    handler.set_header('Content-Type', "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    handler.set_header("Content-Disposition", f"attachment; filename={file_name}.xlsx")

    if not data and not header:
        await handler.finish()
        return

    # header from first of data if not present
    if not header:
        header = ",".join(data[0].keys())

    # header struct: "{name}:{title},..."
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

    output.seek(0)
    handler.write(output.read())
    await handler.finish()
