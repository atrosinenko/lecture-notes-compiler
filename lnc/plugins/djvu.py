from __future__ import unicode_literals

import os
import os.path
import glob
import errno

from lnc.lib.options import get_option, check_target_options
from lnc.lib.process import cmd_try_run, cmd_run, _COMMAND_NOT_FOUND_MSG
from lnc.lib.io import mkdir_p, filter_regexp, needs_update
from lnc.lib.exceptions import ProgramError


def test(conf, target):
    check_target_options(conf, target, ["in-cache-dir",
                                        "out-cache-dir",
                                        "djvu-file"
                                       ])

    cmd_try_run("c44",
                fail_msg=_COMMAND_NOT_FOUND_MSG.format(command="c44",
                                                      package="DjVuLibre")
                )
    cmd_try_run("djvm",
                fail_msg=_COMMAND_NOT_FOUND_MSG.format(command="djvm",
                                                      package="DjVuLibre"))


def before_tasks(conf, target):
    out_cache_dir = get_option(conf, target, "out-cache-dir")
    djvu_file = get_option(conf, target, "djvu-file")

    mkdir_p(out_cache_dir)
    mkdir_p(os.path.dirname(djvu_file))


def handler(info):
    try:
        os.remove(info["output"])
    except OSError as err:
        if err.errno != errno.ENOENT:
            raise
    cmd_run(["c44", info["input"], info["output"]])


def get_tasks(conf, target):
    in_cache_dir = get_option(conf, target, "in-cache-dir")
    out_cache_dir = get_option(conf, target, "out-cache-dir")

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


def after_tasks(conf, target):
    out_cache_dir = get_option(conf, target, "out-cache-dir")
    djvu_file = get_option(conf, target, "djvu-file")

    input_files = sorted(glob.glob(os.path.join(out_cache_dir, "*.djvu")))
    if len(input_files) == 0:
        raise ProgramError(_("No input files."))
    cmd_run(["djvm", "-create", djvu_file] + input_files)
