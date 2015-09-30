from __future__ import unicode_literals

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


class NotesCompiler:
    def __init__(self,ui, program_dir, project_dir, output_name):
        """
        'program_dir' is a base directory of the program (as string)
                      that contains the main configuration file
        'project_dir' is a base directory of project
        'output_name' is a common output file name to which various
                      extensions will be added
        """
        self.ui = ui
        self.program_dir = program_dir
        self.project_dir = project_dir
        self.output_name = output_name
        defaults = {
                "_OUTPUT": self.output_name,
                "_PROJECT": self.project_dir,
                "_SEP": os.sep
        }
        self.conf = ConfigParser.SafeConfigParser(defaults)


    def _load_plugins(self):
        # Load all plug-ins listed in config
        self.plugins = dict()
        for section in self.conf.sections():
            if not _is_plugin_load_section(section):
                continue
            plugname = section[2:-2]
            if not _check_plugin_name(plugname):
                self.ui.warning(_("Plugin name should only contain letters, digits"
                             "and underscores. Plugin '{plugname}' "
                             "was not loaded.").format(plugname=plugname))
            try:
                self.plugins[plugname] = __import__(PACK + ".plugins." + plugname,
                                               fromlist=PACK)
            except ImportError as err:
                self.ui.error(_("Cannot load plugin '{plugname}:\n{error}'")
                         .format(plugname=plugname, error=err))


    def load_global_config(self):
        filename = os.path.join(self.program_dir, "config.ini")
        try:
            with open(filename, "rt") as conffile:
                self.conf.readfp(conffile)
        except (IOError, ConfigParser.Error) as err:
            self.ui.error(_("Error on reading config file {file}:\n{error}").format(file=filename, error=err))

        # Set PATH
        if not self.conf.has_option("global", "PATH"):
            self.ui.error(_("No PATH parameter in config file {file}")
                      .format(file=filename))
        os.environ["PATH"] = self.conf.get("global", "PATH")


    def load_project_config(self):
        filename = os.path.join(self.project_dir, "project.ini")
        try:
            self.conf.read(filename)
        except ConfigParser.Error as err:
            self.ui.error(_("Parsing error for config file {file}:\n{error}").format(file=filename, error=err))

        # Project config file is not allowed to load plug-ins
        for section in self.conf.sections():
            if (_is_plugin_load_section(section) and section[2:-2] not in self.plugins.keys()):
                self.ui.warning(_("Plug-in loading is only possible from "
                        "main config.ini file. Section '{section}' ignored.").
                    format(section=section))
                self.conf.remove_section(section)


    def drop_failed_plugins(self):
        for plugname in self.plugins.keys():
            if self.plugins[plugname] == None:
                self.conf.remove_section("__" + plugname + "__")


    def process_target(self, target_index):
        target = self.targets[target_index]
        msg = get_option(self.conf, target, "__msg__",
            _("Running {target}...").format(target=target))
        self.ui.progress_before(target_index + 1, len(self.targets), msg)
        self.plugins[get_plugin(self.conf, target)].before_tasks(self.conf, target)
        tasks = self.plugins[get_plugin(self.conf, target)].get_tasks(self.conf, target)
        jobs = self.conf.getint("global", "jobs")
        v = Variables(self.ui, target, tasks)
        run_tasks_in_parallel(v, jobs)
        self.ui.progress_after()
        self.plugins[get_plugin(self.conf, target)].after_tasks(self.conf, target)
        self.ui.progress_finalize()
        if (v.errors):
            exc = [err[1] for
                err in v.errors if
                isinstance(err[0], Exception)]
            self.ui.error("[" + target + "] " + "\n===\n\n".join(exc))


    def do_plugins_pretest(self):
        for target in self.targets:
            try:
                self.plugins[get_plugin(self.conf, target)].test(self.conf, target)
            except ProgramError as err:
                self.ui.error(_("Error for target '{target}':\n{error}").format(target=target, error=err), title=_("Preliminary check error"))


    def run(self):
        self.load_global_config()
        self._load_plugins()
        self.load_project_config()
        self.drop_failed_plugins()
        self.targets = self.conf.get("global", "targets").split()

        self.do_plugins_pretest()
        for target_index in range(len(self.targets)):
            try:
                self.process_target(target_index)
            except ProgramError as err:
                self.ui.progress_finalize(True)
                self.ui.error(_("[{target}] {error}'")
                          .format(target=self.targets[target_index], error=err))
            except KeyboardInterrupt:
                self.ui.progress_finalize(True)
                exit(1)


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


def run_tasks_in_parallel(v, jobs):
    thrs = [WorkerThread(v) for i in xrange(jobs)]
    v.ui.progress_current(0)
    for thread in thrs:
        thread.start()
    for thread in thrs:
        thread.join()
