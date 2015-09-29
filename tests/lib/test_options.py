from __future__ import unicode_literals

from StringIO import StringIO
from ConfigParser import SafeConfigParser
from pytest import raises, fixture

from lnc.lib.exceptions import ProgramError, NoOptionError, PluginError
from lnc.lib.options import get_option, get_int, get_boolean, check_target_options

TEST_CONFIG = """
[__plugin_A__]
var-1: 123
var-2: abc

[target1]
__plugin__ = plugin_A
var-1: 456
var-3: uvw
flag-1: 0
flag-2: yes
flag-3: no
flag-4: true
flag-5: false

[target1a]
__plugin__ = plugin_A
var-1: 456
var-3: uvw

[target2]
__plugin__ = plugin_B
var-1: 231

[target3]
var-A: 321
"""

@fixture()
def conf():
    conf = SafeConfigParser()
    f = StringIO(TEST_CONFIG)
    conf.readfp(f)
    f.close()
    return conf

def test_get_option_overriden(conf):
    assert get_option(conf, "target1", "var-1") == "456"
    assert get_option(conf, "target1", "var-1", "defval") == "456"
    assert get_option(conf, "target1", "var-3") == "uvw"
    assert get_option(conf, "target1", "var-3", "defval") == "uvw"

def test_get_option_base(conf):
    assert get_option(conf, "target1", "var-2") == "abc"
    assert get_option(conf, "target1", "var-2", "defval") == "abc"

def test_get_option_implicit_target(conf):
    assert get_option(conf, "plugin_A", "var-1") == "123"
    assert get_option(conf, "plugin_A", "var-1", "defval") == "123"
    raises(NoOptionError, get_option, conf, "plugin_A", "var-3")
    assert get_option(conf, "plugin_A", "var-3", "defval") == "defval"

def test_get_option_undefined(conf):
    raises(NoOptionError, get_option, conf, "target1", "var-ABC")
    assert get_option(conf, "target1", "var-ABC", "defval") == "defval"

def test_get_option_unknown_plugin(conf):
    raises(PluginError, get_option, conf, "target2", "var-1")
    raises(PluginError, get_option, conf, "target2", "var-1", "defval")
    raises(PluginError, get_option, conf, "target2", "var-X")
    raises(PluginError, get_option, conf, "target2", "var-X", "defval")

    raises(PluginError, get_option, conf, "target3", "var-A")
    raises(PluginError, get_option, conf, "target3", "var-A", "defval")
    raises(PluginError, get_option, conf, "target3", "var-X")
    raises(PluginError, get_option, conf, "target3", "var-X", "defval")

def test_get_option_unknown_target(conf):
    raises(PluginError, get_option, conf, "unknown-target", "var-1")
    raises(PluginError, get_option, conf, "unknown-target", "var-1", "defval")

def test_get_option_int(conf):
    assert get_int(conf, "target1", "var-1") == 456
    assert get_int(conf, "target1", "var-1", 789) == 456
    raises(NoOptionError, get_int, conf, "target1", "var-X")
    assert get_int(conf, "target1", "var-X", 321) == 321

def test_get_option_boolean(conf):
    assert get_boolean(conf, "target1", "flag-1") == False
    assert get_boolean(conf, "target1", "flag-2") == True
    assert get_boolean(conf, "target1", "flag-3") == False
    assert get_boolean(conf, "target1", "flag-4") == True
    assert get_boolean(conf, "target1", "flag-5") == False
    raises(NoOptionError, get_boolean, conf, "target1", "flag-X")
    assert get_boolean(conf, "target1", "flag-X", True) == True

def test_check_target_options(conf):
    # No error
    check_target_options(conf, "target1a",
        ["var-1", "var-3"],
        ["var-1", "var-2", "var-3", "var-X"])

    raises(ProgramError, check_target_options, conf, "target1a",
        ["var-3", "var-X"])
    raises(ProgramError, check_target_options, conf, "target1a",
        ["var-3", "var-X"],
        ["var-1", "var-2", "var-3", "var-X"])
    raises(ProgramError, check_target_options, conf, "target1a",
        ["var-3"],
        ["var-1", "var-X"])

def test_check_target_options_implicit_target(conf):
    # No error
    check_target_options(conf, "plugin_A",
        ["var-1"],
        ["var-1", "var-2", "var-X"])

    raises(ProgramError, check_target_options, conf, "plugin_A",
        ["var-1", "var-X"])
    raises(ProgramError, check_target_options, conf, "plugin_A",
        ["var-1", "var-X"],
        ["var-1", "var-2", "var-X"])
    raises(ProgramError, check_target_options, conf, "plugin_A",
        ["var-1"],
        ["var-1", "var-X"])

def test_check_target_options_bad_plugin(conf):
    raises(PluginError, check_target_options, conf, "target2", ["var-X"])
    raises(PluginError, check_target_options, conf, "target3", ["var-X"])
