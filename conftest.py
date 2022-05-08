from easy_api import configs


def pytest_configure(config):
    # import sys
    # sys._called_from_test = True
    configs.install('easy_api/tests/config_test.yaml')
