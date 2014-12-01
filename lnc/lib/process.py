from __future__ import unicode_literals

from subprocess import check_output, CalledProcessError, call, STDOUT

from lnc.lib.exceptions import ExtCommandError
import os


_COMMAND_NOT_FOUND_MSG = _("Something wrong with '{command}' command. "
                          "Probably {package} is not installed or "
                          "PATH variable in config file is not configured "
                          "properly (see documentation).")


_COMMAND_EXECUTION_FAILURE = _("Some problems with '{command}' "
                               "execution:\n{error}")


def cmd_run(command_line_list, fail_msg=None):
    """Runs the command specified be 'command_line_list' list and shows errors and raises
    ExtCommandError if not found or on non-zero error code.
    """
    if not fail_msg:
        fail_msg = _COMMAND_EXECUTION_FAILURE

    try:
        output = check_output(command_line_list, stderr=STDOUT)
    except OSError as err:
        raise ExtCommandError(fail_msg.format(command=command_line_list,
                                              error=err))
    except CalledProcessError as err:
        raise ExtCommandError(fail_msg.format(command=command_line_list,
                                              error=err) + "\n" +
                              "=== Output: ===\n" +
                              err.output + "\n" +
                              "===============\n" +
                              err)
    return output


def cmd_try_run(cmd, fail_msg=None):
    """Runs 'cmd' and shows error if not found.
    Raises ExtCommandError on errors.
    Warning: use only trusted commands.
    """
    if not fail_msg:
        fail_msg = _COMMAND_EXECUTION_FAILURE

    try:
        call(cmd, stdout=open(os.devnull, "wt"), stderr=STDOUT)
    except OSError as err:
        raise ExtCommandError(fail_msg.format(command=cmd,
                                              error=err))
