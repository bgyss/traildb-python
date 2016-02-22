from libc.stdint cimport uint8_t, uint32_t, uint64_t

cdef extern from "traildb.h":

    ctypedef struct tdb:
        pass

    ctypedef uint32_t tdb_field
    ctypedef uint64_t tdb_val
    ctypedef uint64_t tdb_item

    ctypedef struct tdb_event:
        uint64_t timestamp
        uint64_t num_items
        const tdb_item items[0]

    ctypedef struct tdb_cursor:
        pass

    ctypedef int tdb_error

    tdb *tdb_init()
    tdb_error tdb_open(tdb *db, const char *path)

    const char *tdb_get_field_name(const tdb *db, tdb_field field)

    uint64_t tdb_num_trails(const tdb *db)
    uint64_t tdb_num_events(const tdb *db)
    uint64_t tdb_num_fields(const tdb *db)

    const uint8_t *tdb_get_uuid(const tdb *db, uint64_t trail_id)

    tdb_cursor *tdb_cursor_new(const tdb *db)
    tdb_cursor_free(tdb_cursor *cursor)
    tdb_error tdb_get_trail(tdb_cursor *cursor, uint64_t trail_id)
    tdb_event *tdb_cursor_next(tdb_cursor *cursor)

    const char *tdb_get_value(const tdb *db,
                              tdb_field field,
                              tdb_val val,
                              uint64_t *value_length)
