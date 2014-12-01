from __future__ import unicode_literals

import os
import os.path
import threading
import ConfigParser
import traceback

from lnc.lib.exceptions import ProgramError
from lnc.lib.plugin import get_plugin
from lnc.lib.options import get_option

PACK = "lnc"


def _is_plugin_load_section(name):
    return (len(name) > 4 and name.startswith("__") and name.endswith("__"))


def _check_plugin_name(name):
    return all(ch.isalnum() or ch == "_" for ch in name)


def _load_plugins(ui, conf):
    # Load all plug-ins listed in config
    plugins = dict()
    for section in conf.sections():
        if not _is_plugin_load_section(section):
            continue
        plugname = section[2:-2]
        if not _check_plugin_name(plugname):
            ui.warning(_("Plugin name should only contain letters, digits"
                         "and underscores. Plugin '{plugname}' "
                         "was not loaded.").format(plugname=plugname))
        try:
            plugins[plugname] = __import__(PACK + ".plugins." + plugname,
                                           fromlist=PACK)
        except ImportError as err:
            ui.error(_("Cannot load plugin '{plugname}:\n{error}'")
                     .format(plugname=plugname, error=err))
    return plugins


def _initialize(ui, program_dir, project_dir, output_name):
    defaults = {
            "_OUTPUT": output_name,
            "_PROJECT": project_dir,
            "_SEP": os.sep
    }

    conf = ConfigParser.SafeConfigParser(defaults)

    filename = os.path.join(program_dir, "config.ini")
    try:
        with open(filename, "rt") as conffile:
            conf.readfp(conffile)
    except (IOError, ConfigParser.Error) as err:
        ui.error(_("Error on reading config file {file}:\n{error}").
                 format(file=filename, error=err))

    # Set PATH
    if not conf.has_option("global", "PATH"):
        ui.error(_("No PATH parameter in config file {file}")
                  .format(file=filename))
    os.environ["PATH"] = conf.get("global", "PATH")

    plugins = _load_plugins(ui, conf)

    # Project config file cannot load plug-ins
    filename = os.path.join(project_dir, "project.ini")
    try:
        conf.read(filename)
    except ConfigParser.Error as err:
        ui.error(_("Parsing error for config file {file}:\n{error}")
                  .format(file=filename, error=err))

    # Remove newly added plug-in sections
    for section in conf.sections():
        if (_is_plugin_load_section(section) and
                section[2:-2] not in plugins.keys()):
            ui.warning(_("Plug-in loading is only possible from "
                         "main config.ini file. Section '{section}' ignored.")
                       .format(section=section))
            conf.remove_section(section)

    # Remove failed plug-ins
    for plugname in plugins.keys():
        if plugins[plugname] == None:
            conf.remove_section("__" + plugname + "__")

    return conf, plugins


class WorkerThread(threading.Thread):
    def __init__(self, v):
        threading.Thread.__init__(self)
        self.v = v

    def run(self):
        v = self.v
        while True:
            with v.lock:
                if v.errors or not v.tasks:
                    return
                task = v.tasks.pop()

            try:
                task["__handler__"](task)
            except BaseException as err:
                with v.lock:
                    if isinstance(err, ProgramError):
                        v.errors.append((err, str(err)))
                    else:
                        v.errors.append((err, traceback.format_exc()))
                return

            with v.lock:
                v.done += 1
                v.ui.progress_current(float(v.done) / v.total)


class Variables:
    def __init__(self, ui, target, tasks):
        self.ui = ui
        self.done = 0
        self.total = max(len(tasks), 1)
        self.tasks = tasks
        self.lock = threading.Lock()
        self.target = target
        self.errors = []


def run(ui, program_dir, project_dir, output_name):
    """Dispatches other functions.

    'program_dir' is a base directory of the program (as string)
                  that contains the main configuration file
    'project_dir' is a base directory of project
    'output_name' is a common output file name to which various
                  extensions will be added
    """

    conf, plugins = _initialize(ui, program_dir, project_dir, output_name)

    targets = conf.get("global", "targets").split()

    # Preliminary tests
    for target in targets:
        try:
            plugins[get_plugin(conf, target)].test(conf, target)
        except ProgramError as err:
            ui.error(_("Error for target '{target}':\n{error}")
                            .format(target=target, error=err),
                      title=_("Preliminary check error"),)

    for cur, target in enumerate(targets):
        progress_shown = False
        try:
            msg = get_option(conf, target, "__msg__",
                             _("Running {target}...")
                             .format(target=target))
            ui.progress_before(cur + 1, len(targets), msg)
            progress_shown = True

            plugins[get_plugin(conf, target)].before_tasks(conf, target)
            tasks = plugins[get_plugin(conf, target)].get_tasks(conf, target)

            v = Variables(ui, target, tasks)

            ui.progress_current(0)

            jobs = conf.getint("global", "jobs")
            thrs = [WorkerThread(v) for i in xrange(jobs)]
            for thread in thrs:
                thread.start()
            for thread in thrs:
                thread.join()

            ui.progress_after()
            plugins[get_plugin(conf, target)].after_tasks(conf, target)
            ui.progress_finalize()
            progress_shown = False

            if(v.errors):
                exc = [err[1]
                       for err in v.errors
                       if isinstance(err[0], Exception)]
                ui.error("[" + target + "] " + "\n===\n\n".join(exc))

        except ProgramError as err:
            if(progress_shown):
                ui.progress_finalize(True)
            ui.error(_("[{target}] {error}'")
                      .format(target=target, error=err))
        except KeyboardInterrupt:
            if progress_shown:
                ui.progress_finalize(True)
            exit(1)
