import os
import shutil
import subprocess
import unittest
import datetime

from traildb import TrailDB, TrailDBConstructor
from traildb import TrailDBError, TrailDBCursor

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.cookie = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail.tdb', ['field1', 'field2'])
        cons.add(self.cookie, 1, ['a', '1'])
        cons.add(self.cookie, 2, ['b', '2'])
        cons.add(self.cookie, 3, ['c', '3'])
        cons.finalize()

    def tearDown(self):
        shutil.rmtree('testtrail.tdb', True)

    def test_trails(self):
        db = TrailDB('testtrail.tdb')
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
        for cookie, trail in db.crumbs():
            n += 1
            self.assertEqual(self.cookie, cookie)
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
        db = TrailDB('testtrail.tdb')
        self.assertEqual(['time', 'field1', 'field2'], db.fields)

    def test_cookies(self):
        db = TrailDB('testtrail.tdb')
        self.assertEqual(0, db.cookie_id(self.cookie))
        self.assertEqual(self.cookie, db.cookie(0))
        self.assertTrue(self.cookie in db)


    def test_lexicons(self):
        db = TrailDB('testtrail.tdb')

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

        self.assertEqual((datetime.datetime(1970, 1, 1, 0, 0, 1),
                          datetime.datetime(1970, 1, 1, 0, 0, 3)),
                         db.time_range(parsetime = True))


class TestCons(unittest.TestCase):
    def test_cursor(self):
        cookie = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail.tdb', ['field1', 'field2'])
        cons.add(cookie, 1, ['a', '1'])
        cons.add(cookie, 2, ['b', '2'])
        cons.add(cookie, 3, ['c', '3'])
        cons.add(cookie, 4, ['d', '4'])
        cons.add(cookie, 5, ['e', '5'])
        tdb = cons.finalize()

        trail = tdb.trail(tdb.cookie_id(cookie))
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

        field1_values = [e.field1 for e in tdb.trail(tdb.cookie_id(cookie))]
        self.assertEqual(['a', 'b', 'c', 'd', 'e'], field1_values)

    def test_cursor_parsetime(self):
        cookie = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail.tdb', ['field1'])

        events = [(datetime.datetime(2016, 1, 1, 1, 1), ['1']),
                  (datetime.datetime(2016, 1, 1, 1, 2), ['2']),
                  (datetime.datetime(2016, 1, 1, 1, 3), ['3'])]
        [cons.add(cookie, time, fields) for time, fields in events]
        tdb = cons.finalize()

        timestamps = [e.time for e in tdb.trail(0, parsetime = True)]
        self.assertIsInstance(timestamps[0], datetime.datetime)
        self.assertEqual([time for time, _ in events], timestamps)


    def test_cons(self):
        cookie = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail.tdb', ['field1', 'field2'])
        cons.add(cookie, 123, ['a'])
        cons.add(cookie, 124, ['b', 'c'])
        tdb = cons.finalize()

        self.assertEqual(0, tdb.cookie_id(cookie))
        self.assertEqual(cookie, tdb.cookie(0))
        self.assertEqual(1, tdb.num_trails)
        self.assertEqual(2, tdb.num_events)
        self.assertEqual(3, tdb.num_fields)

        crumbs = list(tdb.crumbs())
        self.assertEqual(1, len(crumbs))
        self.assertEqual(cookie, crumbs[0][0])
        self.assertTrue(tdb[cookie])
        self.assertTrue(cookie in tdb)
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

    def test_append(self):
        # TODO: Currently, values must be larger than 7 bytes due to a
        # bug in the lexicon code. When it's fixed, test also smaller
        # input.

        cookie = '12345678123456781234567812345678'
        cons = TrailDBConstructor('testtrail.tdb', ['field1'])
        cons.add(cookie, 123, ['foobarbaz'])
        tdb = cons.finalize()

        cons = TrailDBConstructor('testtrail2.tdb', ['field1'])
        cons.add(cookie, 124, ['barquuxmoo'])
        cons.append(tdb)
        tdb = cons.finalize()

        self.assertEqual(2, tdb.num_events)
        cookie, trail = list(tdb.crumbs())[0]
        trail = list(trail)
        self.assertEqual([123, 124], [e.time for e in trail])
        self.assertEqual(['foobarbaz', 'barquuxmoo'], [e.field1 for e in trail])


    def tearDown(self):
        shutil.rmtree('testtrail.tdb', True)
        shutil.rmtree('testtrail2.tdb', True)


if __name__ == '__main__':
    unittest.main()
