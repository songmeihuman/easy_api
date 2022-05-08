class PackageExistsError(Exception):
    _package_name = None

    def __init__(self, package_name):
        self._package_name = package_name

    def __str__(self):
        return f"Package {self._package_name} already exists"


class PackageNotFoundError(Exception):
    _package_name = None

    def __init__(self, package_name):
        self._package_name = package_name

    def __str__(self):
        return f"Package {self._package_name} not found"


class SqlExistsError(Exception):
    _sql_name = None

    def __init__(self, sql_name):
        self._sql_name = sql_name

    def __str__(self):
        return f"Sql {self._sql_name} already exists"


class SqlNotFoundError(Exception):
    _sql_name = None

    def __init__(self, package_name):
        self._sql_name = package_name

    def __str__(self):
        return f"Sql {self._sql_name} not found"


class TaskExistsError(Exception):
    _task_name = None

    def __init__(self, name):
        self._task_name = name

    def __str__(self):
        return f"Task {self._task_name} already exists"


class GroupExistsError(Exception):
    _group_name = None

    def __init__(self, name):
        self._group_name = name

    def __str__(self):
        return f"Group {self._group_name} already exists"
