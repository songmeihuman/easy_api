import inspect
import json
import logging

import swagger_ui
from apispec import APISpec, BasePlugin, yaml_utils
from apispec.exceptions import APISpecError
from apispec.ext.marshmallow import MarshmallowPlugin
from tornado.routing import URLSpec

from easy_api import configs

logger = logging.getLogger(__name__)


def install(self, handlers):
    if not configs.swagger.enable:
        logger.info('Swagger is disabled')
        return

    config = generate_swagger_file(handlers=handlers)

    # Start the Swagger UI. Automatically generated swagger.json can also
    # be served using a separate Swagger-service.
    swagger_ui.api_doc(
        self,
        # config_path=SWAGGER_API_OUTPUT_FILE,
        config=config,
        url_prefix=configs.swagger.path,
        title=configs.swagger.title,
    )


# copy from apispec
class TornadoPlugin(BasePlugin):
    """APISpec plugin for Tornado"""

    _spec: APISpec = None

    def init_spec(self, spec: APISpec):
        super(TornadoPlugin, self).init_spec(spec)
        self._spec = spec

    def _operations_from_methods(self, handler_class):
        """Generator of operations described in handler's http methods

        :param handler_class:
        :type handler_class: RequestHandler descendant
        """
        for http_method in yaml_utils.PATH_KEYS:
            method = getattr(handler_class, http_method)
            operation = {"responses": {}, "parameters": []}

            specs = method.__dict__.pop("__easy_specs__", [])
            for spec in specs:
                spec.apply(self._spec, operation)

            operation_doc = yaml_utils.load_yaml_from_docstring(method.__doc__)
            if operation_doc:
                operation.update(operation_doc)
                yield {http_method: operation}

    @staticmethod
    def resolve_path(urlspec, method):
        """Convert Tornado URLSpec to OpenAPI-compliant path.

        :param urlspec:
        :type urlspec: URLSpec
        :param method: Handler http method
        :type method: function
        """
        try:
            regex = urlspec.matcher.regex
            path_tpl = urlspec.matcher._path
            group_count = urlspec.matcher._group_count
        except AttributeError:  # tornado<4.5
            regex = urlspec.regex
            path_tpl = urlspec._path
        if regex.groups:
            if regex.groupindex:
                # urlspec path uses named groups
                sorted_pairs = sorted(
                    ((k, v) for k, v in regex.groupindex.items()), key=lambda kv: kv[1]
                )
                args = [pair[0] for pair in sorted_pairs]
            else:
                args = list(inspect.signature(method).parameters.keys())[1:]

            params = tuple(f"{{{arg}}}" for arg in args)
            path = path_tpl % params[:group_count]
        else:
            path = path_tpl
        if path.count("/") > 1:
            path = path.rstrip("/?*")
        return path

    @staticmethod
    def _extensions_from_handler(handler_class):
        """Returns extensions dict from handler docstring

        :param handler_class:
        :type handler_class: RequestHandler descendant
        """
        return yaml_utils.load_yaml_from_docstring(handler_class.__doc__)

    def path_helper(self, operations, *, urlspec, **kwargs):
        """Path helper that allows passing a Tornado URLSpec or tuple."""
        if not isinstance(urlspec, URLSpec):
            urlspec = URLSpec(*urlspec)
        for operation in self._operations_from_methods(urlspec.handler_class):
            operations.update(operation)
        if not operations:
            raise APISpecError(f"Could not find endpoint for urlspec {urlspec}")
        params_method = getattr(urlspec.handler_class, list(operations.keys())[0])
        operations.update(self._extensions_from_handler(urlspec.handler_class))
        return self.resolve_path(urlspec, params_method)


def generate_swagger_file(handlers):
    """Automatically generates Swagger spec file based on RequestHandler
    docstrings and saves it to the specified file_location.
    """

    # Starting to generate Swagger spec file. All the relevant
    # information can be found from here https://apispec.readthedocs.io/
    spec = APISpec(
        title=configs.swagger.title,
        version=configs.swagger.version,
        openapi_version="3.0.2",
        info=dict(description=configs.swagger.description),
        plugins=[TornadoPlugin(), MarshmallowPlugin()],
        servers=[
            {
                "url": f"http://{configs.server.host}:{configs.server.port}/",
            },
        ],
    )
    # Looping through all the handlers and trying to register them.
    # Handlers without docstring will raise errors. That's why we
    # are catching them silently.

    # signature(handler.post).return_annotation.json_schema()
    for handler_tuple in handlers:
        try:
            spec.path(urlspec=handler_tuple)
        except APISpecError as e:
            logger.warning("Handler %s has no docstring: %s", handler_tuple, str(e))

    # Saving the spec file to the specified location.
    # Many be a better way to debug this.
    if configs.swagger.swagger_file_path:
        with open(configs.swagger.swagger_file_path, "w", encoding="utf-8") as file:
            json.dump(spec.to_dict(), file, ensure_ascii=False, indent=4)

    return spec.to_dict()
