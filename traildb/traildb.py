import os
import sys

from collections import namedtuple, defaultdict
from collections import Mapping
from ctypes import c_char, c_char_p, c_ubyte, c_int, c_void_p
from ctypes import c_uint, c_uint8, c_uint32, c_uint64
from ctypes import Structure
from ctypes import CDLL, CFUNCTYPE, POINTER, pointer
from ctypes import byref, cast, string_at, addressof
from datetime import datetime
import time

if os.name == "posix" and sys.platform == "darwin":
    lib = CDLL('libtraildb.dylib')
elif os.name == "posix" and "linux" in sys.platform:
    lib = CDLL('libtraildb.so')

def api(fun, args, res=None):
    fun.argtypes = args
    fun.restype = res

tdb         = c_void_p
tdb_cons    = c_void_p
tdb_field   = c_uint32
tdb_val     = c_uint64
tdb_item    = c_uint64
tdb_cursor  = c_void_p
tdb_error   = c_int

class tdb_event(Structure):
    _fields_ = [("timestamp", c_uint64),
                ("num_items", c_uint64),
                ("items", POINTER(tdb_item))]


api(lib.tdb_cons_init, [], tdb_cons)
api(lib.tdb_cons_open, [tdb_cons, c_char_p, POINTER(c_char_p), c_uint64], tdb_error)
api(lib.tdb_cons_close, [tdb_cons])
api(lib.tdb_cons_add,
    [tdb_cons, POINTER(c_ubyte), c_uint64, POINTER(c_char_p), POINTER(c_uint64)],
    tdb_error)
api(lib.tdb_cons_append, [tdb_cons, tdb], tdb_error)
api(lib.tdb_cons_finalize, [tdb_cons], tdb_error)

api(lib.tdb_init, [], tdb)
api(lib.tdb_open, [tdb, c_char_p], tdb_error)
api(lib.tdb_close, [tdb])

api(lib.tdb_lexicon_size, [tdb, tdb_field], tdb_error)

api(lib.tdb_get_field, [tdb, c_char_p], tdb_error)
api(lib.tdb_get_field_name, [tdb, tdb_field], c_char_p)

api(lib.tdb_get_item, [tdb, tdb_field, POINTER(c_char), c_uint64], tdb_item)
api(lib.tdb_get_value, [tdb, tdb_field, tdb_val, POINTER(c_uint64)], POINTER(c_char))
api(lib.tdb_get_item_value, [tdb, tdb_item, POINTER(c_uint64)], POINTER(c_char))

api(lib.tdb_get_uuid, [tdb, c_uint64], POINTER(c_ubyte))
api(lib.tdb_get_trail_id, [tdb, POINTER(c_ubyte), POINTER(c_uint64)], tdb_error)

api(lib.tdb_error_str, [tdb_error], c_char_p)

api(lib.tdb_num_trails, [tdb], c_uint64)
api(lib.tdb_num_events, [tdb], c_uint64)
api(lib.tdb_num_fields, [tdb], c_uint64)
api(lib.tdb_min_timestamp, [tdb], c_uint64)
api(lib.tdb_max_timestamp, [tdb], c_uint64)

api(lib.tdb_version, [tdb], c_uint64)

api(lib.tdb_cursor_new, [tdb], tdb_cursor)
api(lib.tdb_cursor_free, [tdb])
api(lib.tdb_cursor_next, [tdb_cursor], POINTER(tdb_event))
api(lib.tdb_get_trail, [tdb_cursor, c_uint64], tdb_error)
api(lib.tdb_get_trail_length, [tdb_cursor], c_uint64)


def uuid_hex(uuid):
    if isinstance(uuid, basestring):
        return uuid
    return string_at(uuid, 16).encode('hex')

def uuid_raw(uuid):
    if isinstance(uuid, basestring):
        return (c_ubyte * 16).from_buffer_copy(uuid.decode('hex'))
    return uuid

def nullterm(strs, size):
    return '\x00'.join(strs) + (size - len(strs) + 1) * '\x00'


# Port of tdb_item_field and tdb_item_val in tdb_types.h. Cannot use
# them directly as they are inlined functions.

def tdb_item_is32(item): return not (item & 128)
def tdb_item_field32(item): return item & 127
def tdb_item_val32(item): return (item >> 8) & 4294967295L # UINT32_MAX

def tdb_item_field(item):
    """Return field-part of an item."""
    if tdb_item_is32(item):
        return tdb_item_field32(item)
    else:
        return (item & 127) | (((item >> 8) & 127) << 7)

def tdb_item_val(item):
    """Return value-part of an item."""
    if tdb_item_is32(item):
        return tdb_item_val32(item)
    else:
        return item >> 16

class TrailDBError(Exception):
    """TrailDB error condition."""
    pass

class TrailDBConstructor(object):
    """Construct a new TrailDB."""

    def __init__(self, path, ofields=()):
        """Initialize a new TrailDB constructor.

        path -- TrailDB output path (without .tdb).
        ofields -- List of field (names) in this TrailDB.
        """
        if not path:
            raise TrailDBError("Path is required")
        n = len(ofields)

        ofield_names = (c_char_p * n)(*[name for name in ofields])

        self._cons = lib.tdb_cons_init()
        if lib.tdb_cons_open(self._cons, path, ofield_names, n) != 0:
            raise TrailDBError("Cannot open constructor")

        self.path = path
        self.ofields = ofields

    def __del__(self):
        if hasattr(self, '_cons'):
            lib.tdb_cons_close(self._cons)

    def add(self, uuid, tstamp, values):
        """Add an event in TrailDB.

        uuid -- UUID of this event.
        tstamp -- Timestamp of this event (datetime or integer).
        values -- value of each field.
        """
        if isinstance(tstamp, datetime):
            tstamp = int(time.mktime(tstamp.timetuple()))
        n = len(self.ofields)
        value_array = (c_char_p * n)(*values)
        value_lengths = (c_uint64 * n)(*[len(v) for v in values])
        f = lib.tdb_cons_add(self._cons, uuid_raw(uuid), tstamp, value_array,
                             value_lengths)
        if f:
            raise TrailDBError("Too many values: %s" % values[f])

    def append(self, db):
        """Merge an existing TrailDB in this TrailDB.

        db -- an existing TrailDB
        """
        f = lib.tdb_cons_append(self._cons, db._db)
        if f < 0:
            raise TrailDBError("Wrong number of fields: %d" % db.num_fields)
        if f > 0:
            raise TrailDBError("Too many values: %s" % values[f])

    def finalize(self):
        """Finalize this TrailDB. You cannot add new events in this TrailDB
        after calling this function.

        Returns a new TrailDB handle.
        """
        r = lib.tdb_cons_finalize(self._cons)
        if r:
            raise TrailDBError("Could not finalize (%d)" % r)
        return TrailDB(self.path)


class TrailDBCursor(object):
    """
    TrailDBCursor iterates over events of a trail.

    Typically this class is not instantiated directly but it is
    returned by TrailDB.trail().
    """

    def __init__(self, cursor, cls, valuefun, parsetime, only_timestamp):
        self.cursor = cursor
        self.valuefun = valuefun
        self.parsetime = parsetime
        self.cls = cls
        self.only_timestamp = only_timestamp

    def __del__(self):
        if self.cursor:
            lib.tdb_cursor_free(self.cursor)

    def __iter__(self):
        return self

    def next(self):
        """Return the next event in the trail."""
        event = lib.tdb_cursor_next(self.cursor)
        if not event:
            raise StopIteration()

        address = addressof(event.contents.items)
        items = (tdb_item*event.contents.num_items).from_address(address)

        timestamp = event.contents.timestamp
        if self.parsetime:
            timestamp = datetime.fromtimestamp(event.contents.timestamp)
        if self.only_timestamp:
            return timestamp
        elif self.valuefun:
            return self.cls(timestamp, *(self.valuefun(item) for item in items))
        else:
            return self.cls(timestamp, *items)

class TrailDB(object):
    """Query a TrailDB.

    Attributes:

    TrailDB.num_trails -- number of trails
    TrailDB.num_events -- number of events
    TrailDB.num_fields -- number of fields
    """

    def __init__(self, path):
        """Open a TrailDB at path."""
        self._db = db = lib.tdb_init()
        res = lib.tdb_open(self._db, path)
        if res != 0:
            raise TrailDBError("Could not open %s, error code %d" % (path, res))

        self.num_trails = lib.tdb_num_trails(db)
        self.num_events = lib.tdb_num_events(db)
        self.num_fields = lib.tdb_num_fields(db)
        self.fields = [lib.tdb_get_field_name(db, i) for i in xrange(self.num_fields)]
        self._event_cls = namedtuple('event', self.fields, rename=True)
        self._uint64_ptr = pointer(c_uint64())

    def __del__(self):
        if hasattr(self, '_db'):
            lib.tdb_close(self._db)

    def __contains__(self, uuidish):
        """Return True if UUID or Trail ID exists in this TrailDB."""
        try:
            self[uuidish]
            return True
        except IndexError:
            return False

    def __getitem__(self, uuidish):
        """Return a cursor for the given UUID or Trail ID."""
        if isinstance(uuidish, basestring):
            return self.trail(self.get_trail_id(uuidish))
        return self.trail(uuidish)

    def __len__(self):
        """Return the number of trails."""
        return self.num_trails

    def trails(self, **kwds):
        """Iterate over all trails in this TrailDB.

        Keyword arguments are passed to trail()."""
        for i in xrange(len(self)):
            yield self.get_uuid(i), self.trail(i, **kwds)

    def trail(self, i, parsetime=False, rawitems=False, only_timestamp=False):
        """Return a cursor over a single trail.

        i -- Trail ID.
        parsetime=False -- Return datetime objects instead of integer timestamps.
        rawitems=False -- Return integer items instead of string values.
        only_timestamp=False -- Return only timestamps, not event objects.
        """
        cursor = lib.tdb_cursor_new(self._db)
        if lib.tdb_get_trail(cursor, i) != 0:
            raise TrailDBError("Failed to create cursor")

        valuefun = None if rawitems else self.get_item_value
        return TrailDBCursor(cursor,
                             self._event_cls,
                             valuefun,
                             parsetime,
                             only_timestamp)

    def field(self, fieldish):
        """Return a field ID given a field name."""
        if isinstance(fieldish, basestring):
            return self.fields.index(fieldish)
        return fieldish

    def lexicon(self, fieldish):
        """Return values of the given field ID or field name."""
        field = self.field(fieldish)
        return [self.get_value(field, i) for i in xrange(1, self.lexicon_size(field))]

    def lexicon_size(self, fieldish):
        """Return the number of distinct values in the given
        field ID or field name."""
        field = self.field(fieldish)
        value = lib.tdb_lexicon_size(self._db, field)
        if value == 0:
            raise TrailDBError("Invalid field index")
        return value

    def get_item(self, fieldish, value):
        """Return the item corresponding to a field ID or
        a field name and a string value."""
        field = self.field(fieldish)
        item = lib.tdb_get_item(self._db, field, value, len(value))
        if not item:
            raise TrailDBError("No such value: '%s'" % value)
        return item

    def get_item_value(self, item):
        """Return the string value corresponding to an item."""
        value = lib.tdb_get_item_value(self._db, item, self._uint64_ptr)
        if value is None:
            raise TrailDBError("Error reading value, error: %s" % lib.tdb_error(self._db))
        return value[0:self._uint64_ptr.contents.value]

    def get_value(self, fieldish, val):
        """Return the string value corresponding to a field ID or
        a field name and a value ID."""
        field = self.field(fieldish)
        value = lib.tdb_get_value(self._db, field, val, self._uint64_ptr)
        if value is None:
            raise TrailDBError("Error reading value, error: %s" % lib.tdb_error(self._db))
        return value[0:self._uint64_ptr.contents.value]

    def get_uuid(self, trail_id, raw=False):
        """Return UUID given a Trail ID."""
        uuid = lib.tdb_get_uuid(self._db, trail_id)
        if uuid:
            if raw:
                return string_at(uuid, 16)
            else:
                return uuid_hex(uuid)
        raise IndexError("Trail ID out of range")

    def get_trail_id(self, uuid):
        """Return Trail ID given a UUID."""
        ret = lib.tdb_get_trail_id(self._db, uuid_raw(uuid), self._uint64_ptr)
        if ret:
            raise IndexError("UUID '%s' not found" % uuid)
        return self._uint64_ptr.contents.value

    def time_range(self, parsetime=False):
        """Return the time range covered by this TrailDB.

        parsetime=False -- Return time range as integers or datetime objects.
        """
        tmin = self.min_timestamp()
        tmax = self.max_timestamp()
        if parsetime:
            return datetime.fromtimestamp(tmin), datetime.fromtimestamp(tmax)
        return tmin, tmax

    def min_timestamp(self):
        """Return the minimum time stamp of this TrailDB."""
        return lib.tdb_min_timestamp(self._db)

    def max_timestamp(self):
        """Return the maximum time stamp of this TrailDB."""
        return lib.tdb_max_timestamp(self._db)

