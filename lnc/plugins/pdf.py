from __future__ import unicode_literals

import os
import os.path
import errno
import glob

from lnc.lib.options import get_option, check_target_options
from lnc.lib.process import cmd_run, _COMMAND_NOT_FOUND_MSG
from lnc.lib.io import mkdir_p, filter_regexp, needs_update
from lnc.lib.exceptions import ProgramError


def test(conf, target):
    check_target_options(conf, target, ["in-cache-dir",
                                        "out-cache-dir",
                                        "pdf-file"
                                       ])

    cmd_run(["convert", "-version"],
            fail_msg=_COMMAND_NOT_FOUND_MSG.format(command="convert",
                                                  package="ImageMagick"))
    cmd_run(["gs", "--version"],
            fail_msg=_COMMAND_NOT_FOUND_MSG.format(command="gs",
                                                  package="GhostScript"))


def before_tasks(conf, target):
    out_cache_dir = get_option(conf, target, "out-cache-dir")
    pdf_file = get_option(conf, target, "pdf-file")

    mkdir_p(out_cache_dir)
    mkdir_p(os.path.dirname(pdf_file))


def handler(info):
    try:
        os.remove(info["output"])
    except OSError as err:
        if err.errno != errno.ENOENT:
            raise
    cmd_run(["convert", info["input"], info["output"]])


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
                "output": os.path.join(out_cache_dir, "%04d.pdf" % num)
            }
        if needs_update(x["input"], x["output"]):
            res.append(x)
    return res


def after_tasks(conf, target):
    out_cache_dir = get_option(conf, target, "out-cache-dir")
    pdf_file = get_option(conf, target, "pdf-file")

    input_files = sorted(glob.glob(os.path.join(out_cache_dir, "*.pdf")))
    if len(input_files) == 0:
        raise ProgramError(_("No input files."))

    try:
        os.remove(pdf_file)
    except OSError as err:
        if err.errno != errno.ENOENT:
            raise

    cmd_run(["gs",
             "-dNOPAUSE",
             "-dBATCH",
             "-dSAFER",
             "-sDEVICE=pdfwrite",
             "-sOutputFile=%s" % pdf_file
            ] +
            input_files)
