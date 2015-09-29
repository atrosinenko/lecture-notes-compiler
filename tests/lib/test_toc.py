# -*- coding: utf8 -*-
from __future__ import unicode_literals, print_function

from pytest import raises

from lnc.lib.exceptions import ProgramError
from lnc.lib.toc import read_toc, generate_toc, escape

CORRECT_TOC_TEXT = """utf8

1 Chapter 1
* 2 Page 2
* 2 Subchapter 1
** 3 Some other caption
* 4 Subchapter 2
** 5 Page 5

10 Chapter 2
* 12 Another page
15 Not a chapter
100 List of figures
* 1 Figure 1
* 10 Figure 2"""

CORRECT_TOC_PARSED = [
    [1, "Chapter 1",
        [2, "Page 2"],
        [2, "Subchapter 1",
            [3, "Some other caption"]],
        [4, "Subchapter 2",
            [5, "Page 5"]]],
    [10, "Chapter 2",
        [12, "Another page"]],
    [15, "Not a chapter"],
    [100, "List of figures",
        [1, "Figure 1"],
        [10, "Figure 2"]]]

def test_read_toc_correct(tmpdir):
    test_toc = tmpdir.join("test_toc.txt")
    test_toc.write(CORRECT_TOC_TEXT)
    assert read_toc(test_toc.open()) == CORRECT_TOC_PARSED

def check_read_toc_fails(tmpdir, contents):
    test_toc = tmpdir.join("test_toc.txt")
    test_toc.write(contents)
    raises(ProgramError, read_toc, test_toc.open())

def test_read_toc_wrong_encoding(tmpdir):
    check_read_toc_fails(tmpdir, "utff8\n1 Page 1")

_TOC_WRONG_LEVELS = """utf8
1 Chapter 1
** 2 Page 2"""

def test_read_toc_wrong_levels(tmpdir):
    check_read_toc_fails(tmpdir, _TOC_WRONG_LEVELS)

def test_read_toc_malformed_line(tmpdir):
    check_read_toc_fails(tmpdir, "utf8\n1.5 abc\n")
    check_read_toc_fails(tmpdir, "utf8\n1 abc\n* - a\n")
    check_read_toc_fails(tmpdir, "utf8\n-1 abc\n")

def test_read_toc_nonlatin(tmpdir):
    test_toc = tmpdir.join("test_toc.txt")
    test_toc.write_text("utf8\n1 Оглавление\n",
        encoding="utf8")
    assert read_toc(test_toc.open()) == [[1, "Оглавление"]]

def _write_entry(f, level, entry):
    print("(%d %d %s " % (level, entry[0], entry[1]), file=f, end="")
    for e in entry[2:]:
        _write_entry(f, level + 1, e)
    print(")", file=f, end="")

_TOC_FOR_PRINT_TEST = """utf8
1 P 1
* 2 Ch 1.1
** 3 Pg 3
* 4 Ch 1.2
** 4 P 4
5 P 5
"""

def test_print_toc(tmpdir):
    test_toc = tmpdir.join("test_toc.txt")
    test_toc.write(_TOC_FOR_PRINT_TEST)
    test_output = tmpdir.join("test_output.txt")
    generate_toc(str(test_toc),
                 str(test_output),
                 _write_entry,
                 "[",
                 "]")
    res = "[\n(0 1 P 1 (1 2 Ch 1.1 (2 3 Pg 3 ))(1 4 Ch 1.2 (2 4 P 4 )))(0 5 P 5 )]\n"
    assert test_output.check()
    assert test_output.read() == res

def test_escape():
    assert escape("123", "\"'") == "123"
    assert escape("1\"2'3" , "\"'") == "1\\\"2\\'3"
    assert escape("\\12", "") == "\\12"
    assert escape("\\12", "\\") == "\\\\12"
