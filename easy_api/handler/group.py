import logging
from abc import ABC

from easy_api.handler import api
from easy_api.handler.schema.group import GroupRequestSchema
from easy_api.service import group
from easy_api.web import Handler, Result, response_schema, request_schema

logger = logging.getLogger("easy_api.handler.group")


@api(r'/group')
class CreateGroupHandler(Handler, ABC):

    @response_schema(Result)
    @request_schema('data', GroupRequestSchema)
    async def post(self, data: GroupRequestSchema) -> Result:
        """ Create a group.
        ---
        tags: [Easy API]
        summary: create a group
        """
        result = await group.run(data.tasks)
        return Result.success(result)
