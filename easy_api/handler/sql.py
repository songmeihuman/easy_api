import logging
from abc import ABC

from easy_api.handler import api
from easy_api.handler.schema.sql import SQLRequestSchema
from easy_api.schema import Result, response_schema, request_schema
from easy_api.service.sql import create_sql, delete_sql
from easy_api.web import Handler

logger = logging.getLogger("easy_api.handler.sql")


@api(r'/package/(\w+)/sql/(\w+)')
class CreateSQLHandler(Handler, ABC):

    @response_schema(Result)
    @request_schema('data', SQLRequestSchema)
    async def post(self, package_name: str, sql_name: str, data: SQLRequestSchema) -> Result:
        """ Create a sql api.
        ---
        tags: [Easy API]
        summary: Create a sql api
        parameters:
          - name: package_name
            in: path
            required: true
            description: package name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
          - name: sql_name
            in: path
            required: true
            description: sql name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
        """
        jinja_sql = str(data.sql)
        if not jinja_sql:
            return Result.failre(f'sql is empty')

        try:
            await create_sql(package_name, sql_name, sql_jinja=jinja_sql, database=data.database, overwrite=False,
                             mode=data.mode)
            return Result.success("ok")
        except Exception as e:
            logger.exception("create sql error")
            return Result.failre(str(e))

    @response_schema(Result)
    @request_schema('data', SQLRequestSchema)
    async def put(self, package_name: str, sql_name: str, data: SQLRequestSchema) -> Result:
        """ Update a sql api.
        ---
        tags: [Easy API]
        summary: Update a sql api
        parameters:
          - name: package_name
            in: path
            required: true
            description: package name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
          - name: sql_name
            in: path
            required: true
            description: sql name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
        """
        jinja_sql = str(data.sql)
        if not jinja_sql:
            return Result.failre(f'sql is empty')

        try:
            await create_sql(package_name, sql_name, sql_jinja=jinja_sql, overwrite=True, mode=data.mode)
            return Result.success("ok")
        except Exception as e:
            logger.exception("create sql error")
            return Result.failre(str(e))

    @response_schema(Result)
    async def delete(self, package_name: str, sql_name: str) -> Result:
        """ Delete a sql api.
        ---
        tags: [Easy API]
        summary: Delete a sql api
        parameters:
          - name: package_name
            in: path
            required: true
            description: package name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
          - name: sql_name
            in: path
            required: true
            description: sql name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
        """
        await delete_sql(package_name, sql_name)
        return Result.success("ok")
