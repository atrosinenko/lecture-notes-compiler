from __future__ import unicode_literals, print_function

from lnc.plugins.base_plugin import BasePlugin
from lnc.lib.process import cmd_try_run, cmd_run, _COMMAND_NOT_FOUND_MSG
from lnc.lib.toc import escape, generate_toc


def _write_entry(f, level, entry):
    line = "%s(\"%s\" \"#%d\"" % (" " * (4 * level),
                                  escape(entry[1], "\\\""),
                                  entry[0])
    print(line.encode("utf8"), file=f, end="")
    if len(entry) == 2:
        print(")", file=f)
    else:
        print(file=f)
        for e in entry[2:]:
            _write_entry(f, level + 1, e)
        print("%s)" % (" " * (4 * level)), file=f)


class Plugin(BasePlugin):
    def test(self):
        self._check_target_options(["toc-file",
                                    "tmp-file",
                                    "djvu-file"])

        cmd_try_run("djvused",
                    fail_msg=_COMMAND_NOT_FOUND_MSG.format(command="djvused",
                                                           package="DjVuLibre"))

    def before_tasks(self):
        toc_file = self._get_option("toc-file")
        tmp_file = self._get_option("tmp-file")
        djvu_file = self._get_option("djvu-file")

        generate_toc(toc_file, tmp_file, _write_entry,
                     "set-outline\n(bookmarks\n",
                     ")\n.")

        cmd = ["djvused", "-s", "-f", tmp_file, djvu_file]
        cmd_run(cmd)
