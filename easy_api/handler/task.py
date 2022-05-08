import logging
from abc import ABC

from easy_api.handler import api
from easy_api.service.task import create_task, delete_task
from easy_api.web import Handler, Result, response_schema

logger = logging.getLogger("easy_api.handler.sql")


@api(r'/package/(\w+)/task/(\w+)')
class CreateTaskHandler(Handler, ABC):

    @response_schema(Result)
    async def post(self, package_name: str, task_name: str) -> Result:
        """ Create a task api.
        ---
        tags: [Easy API]
        summary: Create a task api
        parameters:
          - name: package_name
            in: path
            required: true
            description: package name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
          - name: task_name
            in: path
            required: true
            description: sql name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
        """
        try:
            await create_task(package_name, task_name)
            return Result.success("Create success, you can edit to the source of task in the package")
        except Exception as e:
            logger.exception("create sql error")
            return Result.failre(str(e))

    @response_schema(Result)
    async def delete(self, package_name: str, task_name: str) -> Result:
        """ Delete a task api.
        ---
        tags: [Easy API]
        summary: Delete a task api
        parameters:
          - name: package_name
            in: path
            required: true
            description: package name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
          - name: task_name
            in: path
            required: true
            description: sql name can only be made up by numbers, letters and underline, and must be lowercase.
            schema:
              type: string
        """
        await delete_task(package_name, task_name)
        return Result.success("ok")
