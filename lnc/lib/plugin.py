from __future__ import unicode_literals

import ConfigParser

from lnc.lib.exceptions import ProgramError, PluginError


def get_plugin(conf, target):
    """Returns plugin for the given target.
    If 'conf' has section 'target' and there is no option '__plugin__' in that
    section or no such plug-in found, raises PluginError.
    """
    if conf.has_section(target):
        try:
            plugname = conf.get(target, "__plugin__")
        except ConfigParser.Error as err:
            raise ProgramError(_("There are problems with option '__plugin__' "
                                 "in the '{target}' section:\n{error}")
                               .format(target=target, error=err))
    else:
        plugname = target

    if not conf.has_section("__" + plugname + "__"):
        raise PluginError(_("Unknown plugin: {plugin}.")
                          .format(plugin=plugname))
    return plugname
