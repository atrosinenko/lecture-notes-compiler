from __future__ import print_function, unicode_literals

import sys

class ConsoleUi:
    def __init__(self, bar_length=50):
        self.is_progress_active = False
        self.bar_length = bar_length

    def error(self, msg, code=1, title=_("Error")):
        print("[%s]\n%s" % (title, msg), file=sys.stderr)
        if code is not None:
            exit(code)

    def warning(self, msg, title=_("Warning")):
        print("[%s]\n%s" % (title, msg), file=sys.stderr)

    def progress_before(self, current, total, msg):
        print("[%d / %d] %s" % (current, total, msg))
        print("[%s] <before>" % ("." * self.bar_length), end="")
        self.is_progress_active = True
        sys.stdout.flush()

    def progress_current(self, amount):
        hashes = int(self.bar_length * amount)
        print("\r[%s%s] %d%%          " % (
                "#" * hashes,
                " " * (self.bar_length - hashes),
                100 * amount
            ), end="")
        self.is_progress_active = True
        sys.stdout.flush()

    def progress_after(self):
        print("\r[%s] <after>" % ("/" * self.bar_length), end="")
        self.is_progress_active = True
        sys.stdout.flush()

    def progress_finalize(self, error=False):
        if self.is_progress_active:
            if error:
                print()
            else:
                print("\r%s\r" % (" " * (self.bar_length + 15)), end="")
            sys.stdout.flush()
            self.is_progress_active = False
