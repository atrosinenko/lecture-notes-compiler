from __future__ import print_function, unicode_literals

import sys

_BAR_LEN = 50


def error(msg, code=1, title=_("Error")):
    print("[%s]\n%s" % (title, msg), file=sys.stderr)
    if code is not None:
        exit(code)


def warning(msg, title=_("Warning")):
    print("[%s]\n%s" % (title, msg), file=sys.stderr)


def progress_before(current, total, msg):
    print("[%d / %d] %s" % (current, total, msg))
    print("[%s] <before>" % ("." * _BAR_LEN), end="")
    sys.stdout.flush()


def progress_current(amount):
    hashes = int(_BAR_LEN * amount)
    print("\r[%s%s] %d%%          " % (
            "#" * hashes,
            " " * (_BAR_LEN - hashes),
            100 * amount
        ), end="")
    sys.stdout.flush()


def progress_after():
    print("\r[%s] <after>" % ("/" * _BAR_LEN), end="")
    sys.stdout.flush()


def progress_finalize(error=False):
    if error:
        print()
    else:
        print("\r%s\r" % (" " * (_BAR_LEN + 15)), end="")
    sys.stdout.flush()
