import types

from easy_api.schema import Result


class EasyException(Exception):
    code: int = None
    message: str = None
    message_kwargs: dict = None

    def format(self, **kwargs):
        self.message_kwargs = kwargs
        return self

    def __str__(self):
        return self.message.format(**self.message_kwargs) if self.message_kwargs else self.message

    def to_result(self):
        return Result.failre(str(self), self.code)


def e(name: str, code: int, message: str):
    cls =  types.new_class(name, bases=(EasyException,))
    cls.code = code
    cls.message = message
    cls.__module__ = __name__
    return cls


# common errors, error number start at 9999
UnknownError = e("UnknownError", 9999, "Unknown error")

# package errors, error number start at 9899
PackageExistsError = e("PackageExistsError", 9899, "Package already exists")
PackageNotFoundError = e("PackageNotFoundError", 9898, "Package not found")

# sql errors, error number start at 9799
SQLExistsError = e("SQLExistsError", 9899, "SQL already exists")
SQLNotFoundError = e("SQLNotFoundError", 9898, "SQL not found")

# task errors, error number start at 9699
TaskExistsError = e("TaskExistsError", 9699, "Task already exists")

# group errors, error number start at 9599
GroupExistsError = e("GroupExistsError", 9599, "Group already exists")