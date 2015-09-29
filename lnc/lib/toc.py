from __future__ import unicode_literals, print_function

import os.path

from lnc.lib.exceptions import ProgramError
from lnc.lib.io import mkdir_p


_TOC_READ_ERROR_MSG = _("Error while reading Table of Contents file "
                       "'{file}':\n{error}")

_ENCODING_ERROR_MSG = _("Incorrect encoding name at the first line of file.")

_TOC_WRITE_ERROR_MSG = _("Error while writing temporary "
                        "Table of Contents file '{file}:\n"
                        "{error}'")

_TOC_LINE_FORMAT_ERROR_MSG = _("Line {linenum}: incorrect syntax. Should be:\n"
                              "<several '*'> <page number> <description>")

_TOC_NESTING_ERROR_MSG = _("Any line should be no more one level more nested "
                          "than previous one.")


def _parse_line(filename, line_num, line):
    level = 0
    while level < len(line) and line[level] == '*':
        level += 1

    try:
        if level > 0 and not line[level].isspace():
            raise ProgramError()
        tmp = line[level:].split(None, 1)
        pagenum = int(tmp[0])
        desc = tmp[1]
    except (ProgramError, ValueError, IndexError):
        raise ProgramError(_TOC_READ_ERROR_MSG
                           .format(file=filename,
                                   error=_TOC_LINE_FORMAT_ERROR_MSG.format(
                                        linenum=line_num)))
    return [level, pagenum, desc]


def _parse_file(f, encoding):
    """Returns flat list of lists:
    [
        [level, pagenumber, description],
        [level, pagenumber, description],
        ...
    ]
    Checks that next line is no more than one level more nested than
    previous one.
    """

    lines = [unicode(line.strip(), encoding) for line in f.xreadlines()]

    ret = [_parse_line(f.name, i + 1, line)
           for i, line in enumerate(lines)
           if not (line.isspace() or len(line) == 0)]

    for i in xrange(1, len(ret)):
        if ret[i - 1][0] + 1 < ret[i][0]:
            raise ProgramError(_TOC_READ_ERROR_MSG
                               .format(file=f.name,
                                       error=_TOC_NESTING_ERROR_MSG))
    return ret


def _read_toc(toc_file):
    """Reads Table of Contents from the given file object 'f'.
    Each line in file should be in form
    <'*' x level> <page number> <description>
    'level' of the next line should be at most one '*' larger than that of
    previous line.
    First line should contain encoding name.
    Example:
    === BEGIN ===
    utf8
    1 Chapter 1
    * 2 Page 2
    * 2 Subchapter 1
    ** 3 Some other caption
    10 Chapter 2
    * 12 Another page
    15 Not a chapter
    100 List of figures
    * 1 Figure 1
    * 10 Figure 2
    ==== END ====

    This function returns nested lists like these:
    [
        [1, "Chapter 1",
            [2, "Page 2"],
            [2, "Subchapter 1",
                [3, "Some other caption"]
            ]
        ],
        [10, "Chapter 2",
            [12, "Another page"]
        ],
        ...
    ]
    """

    encoding = toc_file.readline().strip()
    try:
        # Is encoding supported?
        unicode(b"abc123", encoding)
    except LookupError:
        raise ProgramError(_TOC_READ_ERROR_MSG
                           .format(file=toc_file.name,
                                   error=_ENCODING_ERROR_MSG))

    lines = _parse_file(toc_file, encoding)


    def f(pos):
        """Returns [next_pos, partial_result]"""
        level = lines[pos][0]
        ret = [lines[pos][1], lines[pos][2]]
        pos += 1
        while pos < len(lines) and lines[pos][0] > level:
            pos, part = f(pos)
            ret.append(part)
        return pos, ret

    pos = 0
    result = []
    while pos < len(lines):
        pos, part = f(pos)
        result.append(part)
    return result


def generate_toc(input_file_name, output_file_name, entry_writer,
                 header="", footer=""):
    """Generates intermediate format-dependent TOC file (output) from
    simple input file (see documentation for syntax description).

    Output file is written as follows:
    - write 'header'
    - for each TOC entry call 'entry_writer'
      (see doc/internals/toc-generation.txt)
    - write 'footer'
    """
    try:
        with open(input_file_name, "rt") as input_file:
            toc = _read_toc(input_file)
    except IOError as err:
        raise ProgramError(_TOC_READ_ERROR_MSG.format(file=input_file_name,
                                                     error=err))
    mkdir_p(os.path.dirname(output_file_name))

    try:
        with open(output_file_name, "wt") as output_file:
            print(header, file=output_file)
            for entry in toc:
                entry_writer(output_file, 0, entry)
            print(footer, file=output_file)
    except IOError as err:
        raise ProgramError(_TOC_WRITE_ERROR_MSG.format(file=output_file_name,
                                                      error=err))


def escape(line, chars):
    """Escapes characters 'chars' with '\\' in 'line'."""
    def esc_one_char(ch):
        if ch in chars:
            return "\\" + ch
        else:
            return ch

    return u"".join([esc_one_char(ch) for ch in line])
