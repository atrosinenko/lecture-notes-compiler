class ProgramError(Exception):
    """Generic exception class for errors in this program."""
    pass


class PluginError(ProgramError):
    pass


class NoOptionError(ProgramError):
    pass


class ExtCommandError(ProgramError):
    pass
