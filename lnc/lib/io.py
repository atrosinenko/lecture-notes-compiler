from __future__ import unicode_literals

import re
import os.path
import errno

from lnc.lib.exceptions import ProgramError

_IMG_EXT = "(bmp|pnm|jpg|jpeg)"


def filter_regexp(path, regex, error_regex=None):
    """Returns entries in 'path' matched by 'regex' and raises
    exception if there are entries not satisfying 'error_regex'
    (the same as 'regex' if None).
    """
    list_ = os.listdir(path)
    if error_regex is None:
        error_regex = regex
    er = re.compile(error_regex)
    if not all(map(er.match, list_)):
        raise ProgramError(_(
            "Extra elements in the '{dir}' directory: {elems}")
            .format(dir=path, elems=filter(lambda x: not er.match(x), list_)))
    r = re.compile(regex)
    return filter(r.match, list_)


def needs_update(source, dest):
    """Returns True, if 'source' is not at least 10s older than 'dest'."""
    try:
        smt = os.path.getmtime(source)
        dmt = os.path.getmtime(dest)
    except OSError:
        return True
    else:
        return smt + 10 > dmt


def mkdir_p(path):
    """Creates 'path' if it does not exist."""
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise
