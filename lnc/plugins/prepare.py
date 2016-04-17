from __future__ import unicode_literals

import os.path
import ConfigParser

from lnc.plugins.base_plugin import BasePlugin
from lnc.lib.process import cmd_run, _COMMAND_NOT_FOUND_MSG
from lnc.lib.io import mkdir_p, filter_regexp, needs_update, _IMG_EXT
from lnc.lib.exceptions import ProgramError


_DEFAULT_TRANSFORM_OPTIONS = {
    "justconvert": "no",
    "chop-edge": "None",
    "rotate-odd": "0",
    "rotate-even": "0",
    "blur": "10",
    "fuzz": "30"}

_POSSIBLE_TRANSFORM_OPTIONS = set([
    "justconvert",
    "chop-edge",
    "chop-size",
    "chop-background",
    "rotate-odd",
    "rotate-even",
    "blur",
    "fuzz"])


def _check_and_normalize_chop(filename, chop, chop_background):
    POSSIBLE_CHOP_VALUES = set(["north", "east", "south", "west"])

    if "none" in chop and chop != set(["none"]):
        raise ProgramError(_(
            "Error in '{file}' file: "
            "'none' should not be combined with "
            "something other as 'chop-edge' value.")
            .format(file=filename))

    if chop == set(["none"]):
        chop = set([])

    if not chop <= POSSIBLE_CHOP_VALUES:
        raise ProgramError(_(
            "Error in '{file}' file: "
            "incorrect values for 'chop-edge' option: {vals}")
            .format(file=filename, vals=(chop - POSSIBLE_CHOP_VALUES)))

    if not chop_background.isalnum():
        raise ProgramError(_(
            "Error in '{file}' file: "
            "'chop-background' value should contain onle "
            "letters and digits.")
            .format(file=filename))
    return chop


def _get_crop_area(info, chop, chop_size, chop_background, blur, fuzz):
    BORDER_SIZE = 10

    cmd = ["convert",
           info["input"],
           "-background", chop_background]
    for edge in chop:
        if edge in ["north", "south"]:
            sizestr = "0x" + str(chop_size)
        else:
            sizestr = str(chop_size) + "x0"
        cmd += ["-gravity", edge, "-chop", sizestr, "-splice", sizestr]

    cmd += ["-bordercolor", chop_background,
            "-border", "%sx%s" % (BORDER_SIZE, BORDER_SIZE),
            "-virtual-pixel", "edge",
            "-blur", "0x%d" % blur,
            "-fuzz", "%d%%" % fuzz,
            "-trim",
            "-format", "%X %Y %w %h",
            "info:-"]
    output = cmd_run(cmd)

    off_x, off_y, sz_x, sz_y = [int(x) for x in output.split()]

    # Adjust border
    off_x -= BORDER_SIZE
    off_y -= BORDER_SIZE

    # Adjust chop
    if "north" in chop:
        off_y -= chop_size
        sz_y += chop_size
    if "east" in chop:
        sz_x += chop_size
    if "south" in chop:
        sz_y += chop_size
    if "east" in chop:
        off_x -= chop_size
        sz_x += chop_size

    return "%dx%d%+dx%+d" % (sz_x, sz_y, off_x, off_y)


def handler(info):
    config = ConfigParser.SafeConfigParser(_DEFAULT_TRANSFORM_OPTIONS)
    transform_file = info["transform-file"]
    try:
        with open(transform_file, "rt") as conffile:
            config.readfp(conffile)
    except (IOError, ConfigParser.Error) as err:
        raise ProgramError(_(
            "Cannot read config file '{file}':\n{error}")
            .format(file=transform_file, error=err))

    try:
        justconvert = config.getboolean("transform", "justconvert")
        if not justconvert:
            chop = config.get("transform", "chop-edge").split()
            chop = set(map(lambda x: x.lower(), chop))
            if "none" not in chop:
                chop_size = config.getint("transform", "chop-size")
                chop_background = config.get("transform", "chop-background")
            odd = config.getint("transform", "rotate-odd")
            even = config.getint("transform", "rotate-even")
            blur = config.getint("transform", "blur")
            fuzz = config.getint("transform", "fuzz")

        if not set(config.options("transform")) <= _POSSIBLE_TRANSFORM_OPTIONS:
            raise ProgramError(_(
                "Unhandled extra options in '{file}' file: {opts}.")
                .format(file=transform_file,
                        opts=list(set(config.options("transform")) -
                                  _POSSIBLE_TRANSFORM_OPTIONS)))
    except (ConfigParser.Error, ValueError) as err:
        raise ProgramError(_(
            "Incorrect '{file}' file:\n{error}")
            .format(file=transform_file, error=err))

    if justconvert:
        cmd_run(["convert", info["input"], info["output"]])
        return

    chop = _check_and_normalize_chop(transform_file, chop, chop_background)

    if info["num"] % 2 == 0:
        angle = even
    else:
        angle = odd

    cmd = ["convert",
           info["input"],
           "-crop", _get_crop_area(info, chop, chop_size,
                                   chop_background, blur, fuzz),
           "+repage",
           "-rotate", str(angle),
           info["output"]]
    cmd_run(cmd)


class Plugin(BasePlugin):
    def test(self):
        self._check_target_options(["pages-dir",
                                    "input-dir",
                                    "transform-file"])
        # Check for presence of ImageMagick
        cmd_run(["convert", "-version"], fail_msg=_COMMAND_NOT_FOUND_MSG.format(
            command="convert",
            package="ImageMagick"))

    def before_tasks(self):
        pages_dir = self._get_option("pages-dir")

        mkdir_p(pages_dir)

        # Temporarily disable multithreading because
        # ImageMagick handles this by itself
        jobs = self.conf.get("global", "jobs")
        self.conf.set("global", "__saved-jobs", jobs)
        self.conf.set("global", "jobs", "1")

    def get_tasks(self):
        input_dir = self._get_option("input-dir")
        pages_dir = self._get_option("pages-dir")
        transform_file = self._get_option("transform-file")

        dirs = filter_regexp(input_dir, r"^[0-9]+-[0-9]+$")

        # Handle multiple files in different input subdirectories
        input_files = {}
        for subdir in sorted(dirs):
            img_re = r"^[0-9]+[.]" + _IMG_EXT + "$"
            images = filter_regexp(os.path.join(input_dir, subdir),
                                   img_re,
                                   "(%s)|(%s)" % (img_re, transform_file))
            for image_file in images:
                num = int(image_file[:image_file.index(".")])
                input_files[num] = os.path.join(input_dir, subdir, image_file)

        res = []
        for num in input_files.keys():
            input_file_dir = os.path.dirname(input_files[num])
            x = {
                    "__handler__": handler,
                    "input": input_files[num],
                    "output": os.path.join(pages_dir, "%04d.pnm" % num),
                    "num": num,
                    "transform-file": os.path.join(input_file_dir,
                                                   transform_file)
                }
            if (needs_update(x["input"], x["output"]) or
                    needs_update(x["transform-file"], x["output"])):
                res.append(x)
        return res

    def after_tasks(self):
        saved_jobs = self.conf.get("global", "__saved-jobs")
        self.conf.set("global", "jobs", saved_jobs)
        self.conf.remove_option("global", "__saved-jobs")
