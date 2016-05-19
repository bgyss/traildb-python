import sys
from random import random
from traildb import TrailDB, TrailDBConstructor

def extract(tdb, cons, sample_size):
    for uuid, trail in tdb.trails():
        if random() < sample_size:
            for event in trail:
                cons.add(uuid, event.time, list(event)[1:])
    return cons.finalize()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: extract_sample source_tdb destination_tdb sample_percentage'
        sys.exit(1)
    tdb = TrailDB(sys.argv[1])
    cons = TrailDBConstructor(sys.argv[2], tdb.fields[1:])
    num = extract(tdb, cons, float(sys.argv[3]) / 100.).num_trails
    print 'Extracted %d trails to %s' % (num, sys.argv[2])
