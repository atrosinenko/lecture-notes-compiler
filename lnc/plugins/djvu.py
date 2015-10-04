from __future__ import unicode_literals

import os.path
import glob
import errno

from lnc.plugins.base_plugin import BasePlugin
from lnc.lib.process import cmd_try_run, cmd_run, _COMMAND_NOT_FOUND_MSG
from lnc.lib.io import mkdir_p, filter_regexp, needs_update
from lnc.lib.exceptions import ProgramError


def handler(info):
    try:
        os.remove(info["output"])
    except OSError as err:
        if err.errno != errno.ENOENT:
            raise
    cmd_run(["c44", info["input"], info["output"]])


class Plugin(BasePlugin):
    def test(self):
        self._check_target_options(["in-cache-dir",
                                    "out-cache-dir",
                                    "djvu-file"])

        cmd_try_run("c44",
                    fail_msg=_COMMAND_NOT_FOUND_MSG.format(command="c44",
                                                          package="DjVuLibre")
                    )
        cmd_try_run("djvm",
                    fail_msg=_COMMAND_NOT_FOUND_MSG.format(command="djvm",
                                                          package="DjVuLibre"))

    def before_tasks(self):
        out_cache_dir = self._get_option("out-cache-dir")
        djvu_file = self._get_option("djvu-file")

        mkdir_p(out_cache_dir)
        mkdir_p(os.path.dirname(djvu_file))

    def get_tasks(self):
        in_cache_dir = self._get_option("in-cache-dir")
        out_cache_dir = self._get_option("out-cache-dir")

        imgs = filter_regexp(in_cache_dir, r"^[0-9]+[.].*$")
        res = []
        for img in imgs:
            num = int(img[:img.index(".")])
            x = {
                    "__handler__": handler,
                    "input": os.path.join(in_cache_dir, img),
                    "output": os.path.join(out_cache_dir, "%04d.djvu" % num)
                }
            if needs_update(x["input"], x["output"]):
                res.append(x)
        return res

    def after_tasks(self):
        out_cache_dir = self._get_option("out-cache-dir")
        djvu_file = self._get_option("djvu-file")

        input_files = sorted(glob.glob(os.path.join(out_cache_dir, "*.djvu")))
        if len(input_files) == 0:
            raise ProgramError(_("No input files."))
        cmd_run(["djvm", "-create", djvu_file] + input_files)
