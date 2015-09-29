import __builtin__

# Dummy _() function instead of actual one from gettext.
__builtin__._ = lambda x: x
