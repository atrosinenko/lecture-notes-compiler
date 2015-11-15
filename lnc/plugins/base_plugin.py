from lnc.lib.options import get_option, check_target_options
from lnc.lib.process import cmd_run, _COMMAND_NOT_FOUND_MSG


class BasePlugin:
    def __init__(self, conf, target):
        self.conf = conf
        self.target = target

    def test(self):
        pass

    def before_tasks(self):
        pass

    def get_tasks(self):
        return []

    def after_tasks(self):
        pass

    def _get_option(self, option, default=None):
        return get_option(self.conf, self.target, option, default)

    def _check_target_options(self, min_opts, max_opts=None):
        return check_target_options(self.conf, self.target, min_opts, max_opts)
