import functools


def authorize(package_name: str, name: str):
    """
    Authorize a package to use the API.

    :param package_name: The package name.
    :param name: The sql name or the task name.
    :return: True if the user is authorized to use the API.
    """

    def authorize_decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Check if the user is authorized to use the API.
            return await func(*args, **kwargs)

        return wrapper

    return authorize_decorator
