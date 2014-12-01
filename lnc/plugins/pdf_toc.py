from __future__ import unicode_literals, print_function

import os
import shutil
import base64

from lnc.lib.options import get_option, check_target_options
from lnc.lib.process import cmd_run, _COMMAND_NOT_FOUND_MSG
from lnc.lib.toc import generate_toc


def test(conf, target):
    check_target_options(conf, target, ["toc-file",
                                        "tmp-file",
                                        "pdf-file",
                                        "pdf-tmp-file"
                                       ])

    cmd_run(["gs", "--version"],
            fail_msg=_COMMAND_NOT_FOUND_MSG.format(command="gs",
                                                  package="GhostScript"))


def _write_entry(f, level, entry):
    if len(entry) > 2:
        count_str = "/Count %d " % ((len(entry) - 2) * -1)
    else:
        count_str = ""

    title = base64.b16encode((entry[1][0:125]).encode("utf-16be"))
    print("%s[%s/Title <FEFF%s> /Page %d /OUT pdfmark" %
            (" " * (4 * level),
             count_str,
             title,
             entry[0]),
          file=f)

    for e in entry[2:]:
        _write_entry(f, level + 1, e)


def before_tasks(conf, target):
    toc_file = get_option(conf, target, "toc-file")
    tmp_file = get_option(conf, target, "tmp-file")
    pdf_file = get_option(conf, target, "pdf-file")
    pdf_tmp_file = get_option(conf, target, "pdf-tmp-file")

    generate_toc(toc_file, tmp_file, _write_entry)

    cmd = ["gs",
           "-dNOPAUSE",
           "-dBATCH",
           "-q",
           "-dSAFER",
           "-sDEVICE=pdfwrite",
           "-sOutputFile=%s" % pdf_tmp_file,
           pdf_file,
           tmp_file]

    cmd_run(cmd)
    os.remove(pdf_file)
    shutil.move(pdf_tmp_file, pdf_file)


def get_tasks(conf, target):
    return []


def after_tasks(conf, target):
    pass
