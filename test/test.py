import shutil
import subprocess
import unittest

from traildb import TrailDB, TrailDBConstructor

# class TestAPI(unittest.TestCase):
#     def setUp(self):
#         subprocess.Popen(('test/test.sh', 'test.tdb')).wait()
#         self.traildb = TrailDB('test.tdb')

#     def tearDown(self):
#         shutil.rmtree('test.tdb')

#     def test_trails(self):
#         db = self.traildb
#         print list(db.trail(0, ptime=True))
#         print list(db[0])

#         for trail in db:
#             for event in trail:
#                 print event.time, event.z

#         for cookie, trail in db.crumbs():
#             print cookie, len(list(trail))

#     def test_fields(self):
#         db = self.traildb
#         print db.fields

#     def test_cookies(self):
#         db = self.traildb
#         print db.cookie(0)
#         print db.has_cookie_index()
#         print db.cookie_id('12345678123456781234567812345678')
#         #print db.cookie_id('abc')
#         #print 'abc' in db

#     def test_values(self):
#         db = self.traildb
#         print db.value(1, 1)

#     def test_lexicons(self):
#         db = self.traildb
#         print db.lexicon_size(1)
#         print db.lexicon(1)
#         print db.lexicon('z')
#         print dict((f, db.lexicon(f)) for f in db.fields[1:])

#     def test_metadata(self):
#         db = self.traildb
#         print db.time_range()
#         print db.time_range(ptime=True)

#     def test_fold(self):
#         db = self.traildb
#         def fold_fn(db, id, ev, acc):
#             acc.append((id, ev))
#         print db.fold(fold_fn, [])

class TestCons(unittest.TestCase):
    def test_cons(self):
        cookie = '12345678123456781234567812345678'
        cons = TrailDBConstructor('test.tdb', ['field1', 'field2'])
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

        trail = crumbs[0][1]
        self.assertEqual(2, len(trail))

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
        cons = TrailDBConstructor('test.tdb', ['field1'])
        cons.add(cookie, 123, ['foobarbaz'])
        tdb = cons.finalize()

        cons = TrailDBConstructor('test2.tdb', ['field1'])
        cons.add(cookie, 124, ['barquuxmoo'])
        cons.append(tdb)
        tdb = cons.finalize()

        self.assertEqual(2, tdb.num_events)
        cookie, trail = list(tdb.crumbs())[0]
        self.assertEqual([123, 124], [e.time for e in trail])
        self.assertEqual(['foobarbaz', 'barquuxmoo'], [e.field1 for e in trail])


    def tearDown(self):
        shutil.rmtree('test.tdb', True)
        shutil.rmtree('test2.tdb', True)

if __name__ == '__main__':
    unittest.main()
