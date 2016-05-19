import sys
from traildb import TrailDB

SESSION_LIMIT = 30 * 60

def sessions(tdb):
    for i, (uuid, trail) in enumerate(tdb.trails(only_timestamp=True)):
        prev_time = trail.next()
        num_events = 1
        num_sessions = 1
        for timestamp in trail:
            if timestamp - prev_time > SESSION_LIMIT:
                num_sessions += 1
            prev_time = timestamp
            num_events += 1
        print 'Trail[%d] Number of Sessions: %d Number of Events: %d' %\
              (i, num_sessions, num_events)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: tutorial_wikipedia_sessions <wikipedia-history.tdb>'
    else:
        sessions(TrailDB(sys.argv[1]))
