#!/usr/bin/python2
from __future__ import print_function, unicode_literals

import sys
import os.path
import gettext

program_path = os.path.dirname(__file__)

gettext.install("lnc",
                os.path.join(program_path, "lang"),
                unicode=True)

from lnc.main import NotesCompiler
from lnc.ui.cli import ConsoleUi

_USAGE = _("Usage: {scriptname} <project_dir> <output_name>\n"
    "<output_name> should not contain any extension "
    "(will be added automatically).")

if len(sys.argv) != 3:
    print(_USAGE.format(scriptname=sys.argv[0]), file=sys.stderr)
    exit(2)

ui = ConsoleUi()
main = NotesCompiler(ui, program_path, sys.argv[1], sys.argv[2])

main.run()
