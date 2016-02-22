import os
import shutil
import unittest

import traildb
import traildb.ctraildb
#from traildb.ctraildb import TrailDB

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.cookie = '12345678123456781234567812345678'
        cons = traildb.TrailDBConstructor('testtrail.tdb', ['field1', 'field2'])
        cons.add(self.cookie, 1, ['a', '1'])
        cons.add(self.cookie, 2, ['b', '2'])
        cons.add(self.cookie, 3, ['c', '3'])
        cons.finalize()

    def tearDown(self):
        shutil.rmtree('testtrail.tdb', True)

    def test_cookie(self):
        db = traildb.ctraildb.TrailDB('testtrail.tdb')
        self.assertEqual(self.cookie, db.cookie(0))

    def test_decode(self):
        db = traildb.ctraildb.TrailDB('testtrail.tdb')

        self.assertEqual(1, db.num_trails)
        self.assertEqual(3, db.num_events)
        self.assertEqual(3, db.num_fields)

        trail = db.trail(0, decode = False)
        events = list(trail) # Force evaluation of generator
        self.assertEqual(3, len(events))

        print db.num_fields

        self.assertEqual(1, events[0][0])
        self.assertEqual('a', db.decode_value(events[0][1][0])) # field1
        self.assertEqual('1', db.decode_value(events[0][1][1])) # field2

        self.assertEqual('b', db.decode_value(events[1][1][0])) # field1
        self.assertEqual('2', db.decode_value(events[1][1][1])) # field2

        self.assertEqual('c', db.decode_value(events[2][1][0])) # field1
        self.assertEqual('3', db.decode_value(events[2][1][1])) # field2




if __name__ == '__main__':
    unittest.main()
