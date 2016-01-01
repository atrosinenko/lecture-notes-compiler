from __future__ import unicode_literals

import ConfigParser

from lnc.lib.exceptions import ProgramError, NoOptionError
from lnc.lib.plugin import get_plugin


def _get_option(conf, target, option, default=None, func=None):
    """Returns option based on special target options
    and plug-in options. Throws NoOptionError
    in case 'default' is 'None' and no such option found
    nor in plug-in defaults, nor in target options.
    """

    if not func:
        func = conf.get

    plugname = get_plugin(conf, target)

    value = default
    try:
        if conf.has_option("__" + plugname + "__", option):
            value = func("__" + plugname + "__", option)
        if conf.has_section(target) and conf.has_option(target, option):
            value = func(target, option)
    except (ConfigParser.Error, ValueError) as err:
        raise ProgramError(_(
            "Error while getting value for option '{option}' "
            "of target '{target}':\n{error}")
            .format(option=option, target=target, error=err))

    if value == None:
        raise NoOptionError(_(
            "Option '{option}' for '{target}' target is not found.")
            .format(option=option, target=target))

    return value


def check_target_options(conf, target, min_opts, max_opts=None):
    """Check that all the required options from 'min_opts'
    are present for 'target' in 'conf' and there are no options
    not listed in the allowed options list 'max_opts'
    (same as 'min_opts' if None).

    Note that both option sets from 'target' and corresponding
    plugin are considered."""
    def no_special_opts(opts):
        return filter(lambda opt: not opt.startswith("_"), opts)

    plugname = get_plugin(conf, target)
    opts = set(no_special_opts(conf.options("__" + plugname + "__")))
    if conf.has_section(target):
        opts |= set(no_special_opts(conf.options(target)))

    if max_opts is None:
        max_opts = min_opts
    min_opts = set(min_opts)
    max_opts = set(max_opts)

    if not min_opts <= opts:
        raise ProgramError(_(
            "Some mandatory options for target '{target}'"
            "are missing: {opts}.")
            .format(target=target, opts=(min_opts - opts)))
    if not opts <= max_opts:
        raise ProgramError(_(
            "Some extra options are given for target "
            "'{target}: {opts}'.")
            .format(target=target, opts=(opts - max_opts)))


def get_option(conf, target, option, default=None):
    return _get_option(conf, target, option, default, conf.get).strip()


def get_int(conf, target, option, default=None):
    return _get_option(conf, target, option, default, conf.getint)


def get_boolean(conf, target, option, default=None):
    return _get_option(conf, target, option, default, conf.getboolean)
