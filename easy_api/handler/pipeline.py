import logging
from abc import ABC

from easy_api.handler import api
from easy_api.handler.schema.pipeline import PipelineRequestSchema
from easy_api.schema import Result, response_schema, request_schema
from easy_api.service import pipeline
from easy_api.web import Handler

logger = logging.getLogger("easy_api.handler.group")


@api(r'/pipeline')
class PipelineHandler(Handler, ABC):

    @response_schema(Result)
    @request_schema('data', schema=PipelineRequestSchema)
    async def post(self, data: PipelineRequestSchema) -> Result:
        """ Create a pipeline.
        ---
        tags: [Easy API]
        summary: create a pipeline
        """
        result = await pipeline.run(data.tasks)
        return Result.success(result)
