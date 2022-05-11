from abc import ABC

from easy_api.handler import api
from easy_api.schema import Result, response_schema
from easy_api.service.package import create_package
from easy_api.web import Handler


@api(r'/package/(\w+)')
class CreatePackageHandler(Handler, ABC):

    @response_schema(Result)
    async def post(self, package_name: str) -> Result:
        """ Create a package.
        ---
        tags: [Easy API]
        summary: Create a package with package_name.
        parameters:
          - name: package_name
            in: path
            required: true
            description: package name can only be made up by numbers, letters and underline, and must be lowercase.
            example: demo
            schema:
              type: string
        """
        try:
            await create_package(package_name)
            return Result.success("ok")
        except Exception as e:
            return Result.error(e)
