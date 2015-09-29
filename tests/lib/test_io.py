from __future__ import unicode_literals

import time
from pytest import raises

from lnc.lib.exceptions import ProgramError
from lnc.lib.io import filter_regexp, needs_update, mkdir_p

def test_filter_regex(tmpdir):
    p = str(tmpdir)
    re_string = "^dir[0-9]*$"

    assert filter_regexp(p, re_string) == []
    assert filter_regexp(p, ".*", "nonexistent") == []

    tmpdir.mkdir("dir1")
    tmpdir.mkdir("dir2")
    raises(ProgramError, filter_regexp, p, ".*", "nonexistent")
    assert set(filter_regexp(p, re_string)) == set(["dir1", "dir2"])
    assert set(filter_regexp(p, re_string, ".*")) == set(["dir1", "dir2"])

    tmpdir.join("extrafile.txt").write("123")
    raises(ProgramError, filter_regexp, p, re_string)
    assert set(filter_regexp(p, re_string, ".*")) == set(["dir1", "dir2"])
    assert set(filter_regexp(p, ".*")) == set(["dir1", "dir2", "extrafile.txt"])

def test_needs_update(tmpdir):
    old = tmpdir.join("old.txt")
    new = tmpdir.join("new.txt")
    old.write("")
    new.write("")
    oldname = str(old)
    newname = str(new)

    t = time.time()
    old.setmtime(t - 15)
    new.setmtime(t)
    assert needs_update(newname, oldname)
    assert not needs_update(oldname, newname)
    old.setmtime(t)
    assert needs_update(oldname, newname)

def test_mkdir_p(tmpdir):
    dir1 = tmpdir.join("dir1")
    dir2 = tmpdir.mkdir("dir2")
    f = dir2.join("file.txt")
    f.write("123")

    assert not dir1.check()
    assert f.check
    mkdir_p(str(dir1))
    assert dir1.check()
    assert f.check()
    mkdir_p(str(dir2))
    assert dir1.check()
    assert f.check()
