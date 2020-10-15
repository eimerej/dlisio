"""
Testing monkey patching done by user (new classes or different
attributes processing or similar)
"""
import pytest

from dlisio.plumbing import valuetypes, linkage
from dlisio.plumbing import Channel
from dlisio.plumbing import Parameter

import dlisio

from collections import namedtuple
Attr = namedtuple('attr', ['values', 'units'], defaults=[[], None])

class ActuallyKnown(dlisio.plumbing.basicobject.BasicObject):
    attributes = {
        "SOME_LIST"   : valuetypes.vector,
        "SOME_VALUE"  : valuetypes.scalar,
        "SOME_STATUS" : valuetypes.boolean,
    }

    def __init__(self, obj = None, name = None, lf = None):
        super().__init__(obj, name = name, type = "UNKNOWN_SET", lf = lf)

    @property
    def list(self):
        return self['SOME_LIST']

    @property
    def value(self):
        return self['SOME_VALUE']

    @property
    def status(self):
        return self['SOME_STATUS']

def test_type_new(f):
    assert len(f.unknowns) == 2
    unknown = f.object('UNKNOWN_SET', 'OBJ1', 10, 0)
    with pytest.raises(AttributeError):
        assert unknown.value == "VAL1"

    try:
        f.types['UNKNOWN_SET'] = ActuallyKnown
        f.load()

        unknown = f.object('UNKNOWN_SET', 'OBJ1', 10, 0)

        assert unknown.list == ["LIST_V1", "LIST_V2"]
        assert unknown.value == "VAL1"
        assert unknown.status == True

        assert len(f.unknowns) == 1
    finally:
        del f.types['UNKNOWN_SET']

def test_type_change(f):
    try:
        # Parse all parameters as if they where Channels
        dlisio.dlis.types['PARAMETER'] = dlisio.plumbing.Channel
        f.load()

        longname = f.object('LONG-NAME', 'PARAM1-LONG', 10, 0)
        axis     = f.object('AXIS', 'AXIS1', 10, 0)
        obj      = f.object('PARAMETER', 'PARAM1', 10, 0)

        # obj should have been parsed as a Channel
        assert isinstance(obj, dlisio.plumbing.Channel)

        # Parameter attributes that's also Channel attributes should be
        # parsed normally
        assert obj.long_name         == longname
        assert obj.dimension         == [2]
        assert obj.axis              == [axis]

        # Parameter attributes that's not in Channel should end up in stash
        assert obj.stash['VALUES']   == [101, 120]
        assert obj.stash['ZONES']    == [(10, 0, 'ZONE-A')]

    finally:
        # even if the test fails, make sure that types is reset to its default,
        # to not interfere with other tests
        dlisio.dlis.types['PARAMETER'] = dlisio.plumbing.Parameter

def test_type_removal(f):
    try:
        # Deleting object-type CHANNEL and reload
        del dlisio.dlis.types['CHANNEL']
        f.load()

        obj = f.object('CHANNEL', 'CHANN1', 10, 0)

        # Channel should be parsed as Unknown, but the type should still
        # reflects what's on file
        assert isinstance(obj, dlisio.plumbing.Unknown)
        assert obj.fingerprint in f.unknowns['CHANNEL']
        assert obj.type == 'CHANNEL'

    finally:
        # even if the test fails, make sure that types is reset to its default,
        # to not interfere with other tests
        f.types['CHANNEL'] = dlisio.plumbing.Channel

    # Channels should now be parsed as Channel.allobjects
    assert 'CHANNEL' not in f.unknowns

def test_attribute_change_in_instance():
    ch1 = Channel()
    ch1.attic['PROPERTIES'] = Attr([10])

    ch2 = Channel()
    ch2.attic['PROPERTIES'] = Attr([10])

    # Change properties to be parsed as scalar (not vector)
    ch1.attributes = dict(ch1.attributes)
    ch1.attributes['PROPERTIES'] = valuetypes.scalar

    assert ch1.properties == 10

    # check that other object of the same type is not affected
    assert ch2.properties == [10]

def test_attribute_change_in_class():
    ch1 = Channel()
    ch1.attic['PROPERTIES'] = Attr([10])

    ch2 = Channel()
    ch2.attic['PROPERTIES'] = Attr([10])

    try:
        # Change properties to be parsed as scalar (not vector)
        original = dict(Channel.attributes)
        Channel.attributes['PROPERTIES'] = valuetypes.scalar

        # The change should be observable on all newly created objects
        assert ch2.properties == 10
        assert ch2.properties == 10
    finally:
        Channel.attributes = original

def test_linkage_change_in_instance(f, assert_log):
    ch1  = f.object('CHANNEL', 'CHANN1')
    ch2  = f.object('CHANNEL', 'CHANN2')
    tool = f.object('TOOL', 'TOOL1')

    assert ch1.source == tool
    assert ch2.source == tool

    try:
        # Change linkage rule for source from objref to obname('FRAME')
        ch1.linkage = dict(ch1.linkage)
        ch1.linkage['SOURCE'] = linkage.obname('FRAME')

        # Attic is still objref, so creating reference to object should fail.
        # source return value from attic and warning is issued.
        assert ch1.source == None
        assert_log('Unable to create object-reference')

        # check that other object of the same type is not affected
        assert ch2.source == tool
    finally:
        ch1.linkage = Channel.linkage

def test_linkage_change_in_class(f, assert_log):

    #Reload file for change to take effect
    f.load()
    p1 = f.object('PARAMETER', 'PARAM1')
    p2 = f.object('PARAMETER', 'PARAM3')

    try:
        # Change how SOURCE is parsed for all Channels
        original = dict(Parameter.linkage)
        Parameter.linkage['AXIS'] = linkage.objref
        # Attic is still obname, so creating reference to object should fail.
        # source return value from attic and warning is issued.
        assert p1.axis == [None]
        assert p2.axis == [None, None]
        assert_log('Unable to create object-reference')
    finally:
        Parameter.linkage = original
        f.load()
