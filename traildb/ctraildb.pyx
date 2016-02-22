from libc.stdint cimport uint64_t

cimport traildb

cdef uint64_t tdb_item_is32(item): return not (item & 128)
cdef uint64_t tdb_item_field32(item): return item & 127
cdef uint64_t tdb_item_val32(item): return (item >> 8) & 2147483647 # UINT32_MAX


cdef tdb_item_field(item):
    if tdb_item_is32(item):
        return tdb_item_field32(item)
    else:
        return (item & 127) | (((item >> 8) & 127) << 7)

cdef tdb_item_val(item):
    if tdb_item_is32(item):
        return tdb_item_val32(item)
    else:
        return item >> 16


cdef class TrailDB:
    cdef traildb.tdb* _tdb
    cdef public uint64_t num_trails
    cdef public uint64_t num_events
    cdef public uint64_t num_fields

    def __cinit__(self):
        self._tdb = traildb.tdb_init()

    def __init__(self, path):
        res = traildb.tdb_open(self._tdb, path)
        print "res", res
        if res != 0:
            raise Exception("oops, tdb_open failed")

        self.num_trails = traildb.tdb_num_trails(self._tdb)
        self.num_events = traildb.tdb_num_events(self._tdb)
        self.num_fields = traildb.tdb_num_fields(self._tdb)


    def crumbs(self, **kwds):
        for i in xrange(self.num_trails):
            yield self.cookie(i), self.trail(i, **kwds)

    def cookie(self, i):
        cookie = traildb.tdb_get_uuid(self._tdb, i)
        if cookie:
            return cookie[:16].encode('hex')

        raise IndexError("Cookie index out of range")


    def trail(self, i, parsetime = False, decode = False):
        cdef traildb.tdb_cursor *cursor = traildb.tdb_cursor_new(self._tdb)
        if traildb.tdb_get_trail(cursor, i) != 0:
            return 0

        cdef const traildb.tdb_event *event
        cdef uint64_t[:] items

        while True:
            event = traildb.tdb_cursor_next(cursor)
            if event == NULL:
                return

            items = <uint64_t[:event.num_items]>event.items
            yield (event.timestamp, items)

        return

    def decode_value(self, item):
        field = tdb_item_field(item)
        val = tdb_item_val(item)

        cdef uint64_t value_size
        value = traildb.tdb_get_value(self._tdb, field, val, &value_size)
        return value[:value_size]

    def field(self, name):
        fields = {}
        for i in range(self.num_fields):
            fields[traildb.tdb_get_field_name(self._tdb, i)] = i

        return fields[name]
