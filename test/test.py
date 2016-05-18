import os
import shutil
import subprocess
import unittest
import datetime

from traildb import TrailDB, TrailDBConstructor, tdb_item_field, tdb_item_val
from traildb import TrailDBError, TrailDBCursor

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.uuid = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail', ['field1', 'field2'])
        cons.add(self.uuid, 1, ['a', '1'])
        cons.add(self.uuid, 2, ['b', '2'])
        cons.add(self.uuid, 3, ['c', '3'])
        cons.finalize()

    def tearDown(self):
        os.unlink('testtrail.tdb')

    def test_trails(self):
        db = TrailDB('testtrail')
        self.assertEqual(1, db.num_trails)

        trail = db.trail(0)
        self.assertIsInstance(trail, TrailDBCursor)

        events = list(trail) # Force evaluation of generator
        self.assertEqual(3, len(events))
        for event in events:
            self.assertTrue(hasattr(event, 'time'))
            self.assertTrue(hasattr(event, 'field1'))
            self.assertTrue(hasattr(event, 'field2'))

    def test_crumbs(self):
        db = TrailDB('testtrail.tdb')

        n = 0
        for uuid, trail in db.trails():
            n += 1
            self.assertEqual(self.uuid, uuid)
            self.assertIsInstance(trail, TrailDBCursor)
            self.assertEqual(3, len(list(trail)))

        self.assertEqual(1, n)

    def test_silly_open(self):
        self.assertTrue(os.path.exists('testtrail.tdb'))
        self.assertFalse(os.path.exists('testtrail'))

        db1 = TrailDB('testtrail.tdb')
        db2 = TrailDB('testtrail')

        with self.assertRaises(TrailDBError):
           TrailDB('foo.tdb')

    def test_fields(self):
        db = TrailDB('testtrail')
        self.assertEqual(['time', 'field1', 'field2'], db.fields)

    def test_uuids(self):
        db = TrailDB('testtrail')
        self.assertEqual(0, db.get_trail_id(self.uuid))
        self.assertEqual(self.uuid, db.get_uuid(0))
        self.assertTrue(self.uuid in db)


    def test_lexicons(self):
        db = TrailDB('testtrail')

        # First field
        self.assertEqual(4, db.lexicon_size(1))
        self.assertEqual(['a', 'b', 'c'], db.lexicon(1))

        # Second field
        self.assertEqual(['1', '2', '3'], db.lexicon(2))

        with self.assertRaises(TrailDBError):
            db.lexicon(3) # Out of bounds


    def test_metadata(self):
        db = TrailDB('testtrail.tdb')
        self.assertEqual(1, db.min_timestamp())
        self.assertEqual(3, db.max_timestamp())
        self.assertEqual((1, 3), db.time_range())

        self.assertEqual((1, 3), db.time_range(parsetime = False))


class TestCons(unittest.TestCase):
    def test_cursor(self):
        uuid = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail', ['field1', 'field2'])
        cons.add(uuid, 1, ['a', '1'])
        cons.add(uuid, 2, ['b', '2'])
        cons.add(uuid, 3, ['c', '3'])
        cons.add(uuid, 4, ['d', '4'])
        cons.add(uuid, 5, ['e', '5'])
        tdb = cons.finalize()

        with self.assertRaises(IndexError):
            tdb.get_trail_id('12345678123456781234567812345679')

        trail = tdb.trail(tdb.get_trail_id(uuid))
        with self.assertRaises(TypeError):
            len(trail)

        j = 1
        for event in trail:
            self.assertEqual(j, int(event.field2))
            self.assertEqual(j, int(event.time))
            j += 1
        self.assertEqual(6, j)

        # Iterator is empty now
        self.assertEqual([], list(trail))

        field1_values = [e.field1 for e in tdb.trail(tdb.get_trail_id(uuid))]
        self.assertEqual(['a', 'b', 'c', 'd', 'e'], field1_values)

    def test_cursor_parsetime(self):
        uuid = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail', ['field1'])

        events = [(datetime.datetime(2016, 1, 1, 1, 1), ['1']),
                  (datetime.datetime(2016, 1, 1, 1, 2), ['2']),
                  (datetime.datetime(2016, 1, 1, 1, 3), ['3'])]
        [cons.add(uuid, time, fields) for time, fields in events]
        tdb = cons.finalize()

        timestamps = [e.time for e in tdb.trail(0, parsetime = True)]

        self.assertIsInstance(timestamps[0], datetime.datetime)
        self.assertEqual([time for time, _ in events], timestamps)
        self.assertEquals(tdb.time_range(True),
                          (events[0][0], events[-1][0]))


    def test_cons(self):
        uuid = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail', ['field1', 'field2'])
        cons.add(uuid, 123, ['a'])
        cons.add(uuid, 124, ['b', 'c'])
        tdb = cons.finalize()

        self.assertEqual(0, tdb.get_trail_id(uuid))
        self.assertEqual(uuid, tdb.get_uuid(0))
        self.assertEqual(1, tdb.num_trails)
        self.assertEqual(2, tdb.num_events)
        self.assertEqual(3, tdb.num_fields)

        crumbs = list(tdb.trails())
        self.assertEqual(1, len(crumbs))
        self.assertEqual(uuid, crumbs[0][0])
        self.assertTrue(tdb[uuid])
        self.assertTrue(uuid in tdb)
        self.assertFalse('00000000000000000000000000000000' in tdb)
        with self.assertRaises(IndexError):
            tdb['00000000000000000000000000000000']

        trail = list(crumbs[0][1])

        self.assertEqual(123, trail[0].time)
        self.assertEqual('a', trail[0].field1)
        self.assertEqual('', trail[0].field2) # TODO: Should this be None?

        self.assertEqual(124, trail[1].time)
        self.assertEqual('b', trail[1].field1)
        self.assertEqual('c', trail[1].field2)

    def test_items(self):
        uuid = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail', ['field1', 'field2'])
        cons.add(uuid, 123, ['a', 'x' * 2048])
        cons.add(uuid, 124, ['b', 'y' * 2048])
        tdb = cons.finalize()

        cursor = tdb.trail(0, rawitems=True)
        event = cursor.next()
        self.assertEqual(tdb.get_item_value(event.field1), 'a')
        self.assertEqual(tdb.get_item_value(event.field2), 'x' * 2048)
        self.assertEqual(tdb.get_item('field1', 'a'), event.field1)
        self.assertEqual(tdb.get_item('field2', 'x' * 2048), event.field2)
        event = cursor.next()
        self.assertEqual(tdb.get_item_value(event.field1), 'b')
        self.assertEqual(tdb.get_item_value(event.field2), 'y' * 2048)
        self.assertEqual(tdb.get_item('field1', 'b'), event.field1)
        self.assertEqual(tdb.get_item('field2', 'y' * 2048), event.field2)

        cursor = tdb.trail(0, rawitems=True)
        event = cursor.next()
        field = tdb_item_field(event.field1)
        val = tdb_item_val(event.field1)
        self.assertEqual(tdb.get_value(field, val), 'a')
        field = tdb_item_field(event.field2)
        val = tdb_item_val(event.field2)
        self.assertEqual(tdb.get_value(field, val), 'x' * 2048)
        event = cursor.next()
        field = tdb_item_field(event.field1)
        val = tdb_item_val(event.field1)
        self.assertEqual(tdb.get_value(field, val), 'b')
        field = tdb_item_field(event.field2)
        val = tdb_item_val(event.field2)
        self.assertEqual(tdb.get_value(field, val), 'y' * 2048)

    def test_append(self):
        uuid = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail', ['field1'])
        cons.add(uuid, 123, ['foobarbaz'])
        tdb = cons.finalize()

        cons = TrailDBConstructor('testtrail2', ['field1'])
        cons.add(uuid, 124, ['barquuxmoo'])
        cons.append(tdb)
        tdb = cons.finalize()

        self.assertEqual(2, tdb.num_events)
        uuid, trail = list(tdb.trails())[0]
        trail = list(trail)
        self.assertEqual([123, 124], [e.time for e in trail])
        self.assertEqual(['foobarbaz', 'barquuxmoo'], [e.field1 for e in trail])

    def tearDown(self):
        try:
            os.unlink('testtrail.tdb')
            os.unlink('testtrail2.tdb')
        except:
            pass


if __name__ == '__main__':
    unittest.main()
