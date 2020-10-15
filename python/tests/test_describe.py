"""
Testing 'describe' functionality
"""
from io import StringIO

import dlisio
from dlisio.plumbing import *

def test_describe(fpath):
    # Because the .describe() i.e. returns long descriptive textual string,
    # they are hard to test. But the very least test that it is callable.

    with dlisio.load(fpath) as batch:
        _ = batch.describe()

        for f in batch:
            _ = f.describe()

            for obj in f.match('.*', '.*'):
                _ = obj.describe(indent='   ', width=70, exclude='e')

def test_replist():
    ch1 = Channel(name='TIME')
    ch1.origin = 1
    ch1.copynumber = 0

    ch2 = Channel(name='TDEP')
    ch2.origin = 1
    ch2.copynumber = 1

    channels = [ch1, ch2, None]
    names    = replist(channels, 'name')
    typename = replist(channels, 'typename')
    default  = replist(channels, 'not-a-valid-option')

    assert names    == ['TIME', 'TDEP', 'None']
    assert typename == ['Channel(TIME)', 'Channel(TDEP)', 'None']
    assert default  == ['Channel(TIME, 1, 0)', 'Channel(TDEP, 1, 1)', 'None']

    # Elements that are not a subclass of BasicObjects
    elems = [None , 1, 'str', 2.0]
    reprs = replist(elems, '')
    assert reprs == [str(x) for x in elems]


def test_sampled_attrs():
    attic = {
        'CORRECT' : [1, 2],
        'WRONG'   : [5, 6, 7],
        'VALUES'  : [0.5, 0.6, 0.7, 0.8]
    }
    dims = [2]

    exclude = parseoptions('e')
    buf = StringIO()

    d = OrderedDict()
    d['correct'] = 'CORRECT'
    d['wrong'] = 'WRONG'
    d['drop'] = 'NOT-IN-ATTIC'

    describe_sampled_attrs(
            buf,
            attic,
            dims,
            'VALUES',
            d,
            80,
            ' ',
            exclude
    )

    ref = (' Value(s) : [[0.5 0.6]\n'
           '             [0.7 0.8]]\n'
           ' correct  : 1 2\n'
           '\n'
           ' Invalid dimensions\n'
           ' --\n'
           ' wrong : 5 6 7\n\n'
    )

    assert str(buf.getvalue()) == ref

def test_sampled_attrs_wrong_value():
    attic = {'VALUES' : [0.5, 0.6, 0.7]}
    dims = [2]

    exclude = parseoptions('e')
    buf = StringIO()

    describe_sampled_attrs(
            buf,
            attic,
            dims,
            'VALUES',
            {},
            80,
            ' ',
            exclude
    )

    ref = (
           ' Invalid dimensions\n'
           ' --\n'
           ' Value(s) : 0.5 0.6 0.7\n\n'
    )

    assert str(buf.getvalue()) == ref


def test_describe_header():
    # top level header, indented with one whitespace
    case1 = (' -------\n'
             ' Channel\n'
             ' -------\n'
    )

    # section header, indented with one withspace
    case2 = (' Index\n'
             ' --\n'
    )

    buf = StringIO()
    describe_header(buf, 'Channel', width=10, indent=' ', lvl=1)
    assert str(buf.getvalue()) == case1

    buf = StringIO()
    describe_header(buf, 'Index', 10, ' ', lvl=2)
    assert str(buf.getvalue()) == case2

def test_describe_description():
    ln = Longname()
    from collections import namedtuple
    Attr = namedtuple('attr', ['values', 'units'], defaults=[[], None])

    ln.attic = {
        'QUANTITY'           : Attr(['diameter and stuff']),
        'SOURCE-PART-NUMBER' : Attr([10])
    }
    # description is a Longname object
    case1 = (' Description\n'
             ' --\n'
             ' Quantity           : diameter\n'
             '                      and stuff\n'
             ' Source part number : 10\n\n'
    )

    buf = StringIO()
    exclude = parseoptions('e')
    describe_description(buf, ln, width=31, indent=' ', exclude=exclude)
    assert str(buf.getvalue()) == case1

    # description is a string
    case2 = (' Description : string\n'
             '               desc\n\n'
    )

    buf = StringIO()
    describe_description(buf, 'string desc', width=21, indent=' ',
            exclude=exclude)
    assert str(buf.getvalue()) == case2

def test_describe_dict():
    d = OrderedDict()
    d['desc']  = 'long description'
    d['list']  = list(range(10))
    d['empty'] = None


    # dict, indented with one whitespace, wrapped at 20 characters
    case1 = (' desc  : long\n'
             '         description\n'
             ' list  : 0 1 2 3 4 5\n'
             '         6 7 8 9\n'
             ' empty : None\n\n'
    )

    buf = StringIO()
    exclude = parseoptions('')
    describe_dict(buf, d, width=20, indent=' ', exclude=exclude)
    assert str(buf.getvalue()) == case1

    # dict, indented with one whitespace, wrapped at 20 characters, where empty
    # values are ommited
    case2 = (' desc : long\n'
             '        description\n'
             ' list : 0 1 2 3 4 5\n'
             '        6 7 8 9\n\n'
    )

    buf = StringIO()
    exclude = parseoptions('e')
    describe_dict(buf, d, width=20, indent=' ', exclude=exclude)
    assert str(buf.getvalue()) == case2

def test_describe_text():
    text = 'Desc : fra cha'

    # text, indented with a single withspace, wrap on 11 characters, and
    # subindented such that the 'key' matches up with the above
    case1 = (' Desc : fra\n'
             '        cha\n'
    )

    buf = StringIO()
    describe_text(buf, text, 11, ' ', subindent=''.ljust(8))
    assert str(buf.getvalue()) == case1

    # text, indented with a single withspace, wrap on 11 characters, and no
    # subindent. I.e subindent=indent
    case2 = (' Desc : fra\n'
            ' cha\n'
    )

    buf = StringIO()
    describe_text(buf, text, 11, ' ')
    assert str(buf.getvalue()) == case2

def test_describe_array():
    # describe_array should not write anything to the buffer when supplying an
    # empty array with writempty=False
    buf = StringIO()
    describe_array(buf, [], width=80, indent='  ', subindent='  ',
            writeempty=False)

    assert buf.getvalue() == StringIO().getvalue()

    # wrap array on 10 characters and indent it by one whitespace.
    # describe_array should align columns when the elements are of unequal
    # length
    case1 = (' 100  2000\n'
             ' 3000 10\n')

    buf = StringIO()
    arr = [100, 2000, 3000, 10]
    describe_array(buf, arr, width=10, indent=' ')
    assert str(buf.getvalue()) == case1

def test_describe_ndarray():
    # ndarray's should be handled by numpy's array2string

    # A array where each sample is a 2x2 ndarray, indented by one whitespace
    case1 = (' [[[ 100 2000]\n'
             '   [3000   10]]\n'
             '\n'
             '  [[  20   30]\n'
             '   [3000  200]]]\n')

    arr = np.array([[[100, 2000], [3000, 10]], [[20, 30], [3000, 200]]])
    buf = StringIO()
    describe_array(buf, arr, width=20, indent=' ')
    assert str(buf.getvalue()) == case1

