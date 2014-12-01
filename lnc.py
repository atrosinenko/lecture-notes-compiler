#!/usr/bin/python2
from __future__ import print_function, unicode_literals

import sys
import os.path
import gettext

_PROGRAM_PATH = os.path.dirname(__file__)

gettext.install("lnc",
                os.path.join(_PROGRAM_PATH, "lang"),
                unicode=True)

import lnc.main
import lnc.ui.cli

_USAGE = _("Usage: {scriptname} <project_dir> <output_name>\n"
    "<output_name> should not contain any extension "
    "(will be added automatically).")

if len(sys.argv) != 3:
    print(_USAGE.format(scriptname=sys.argv[0]), file=sys.stderr)
    exit(2)

lnc.main.run(lnc.ui.cli,
                 _PROGRAM_PATH,
                 sys.argv[1],
                 sys.argv[2])
