import sys
import gzip
import hashlib
from datetime import datetime

import traildb

num_events = 0

# This script parses Wikipedia revision metadata that you can find here
# https://dumps.wikimedia.org/enwiki/
# You want a file like
# https://dumps.wikimedia.org/enwiki/20160501/enwiki-20160501-stub-meta-history.xml.gz

def add_event(cons, uuid, tstamp, user, ip, title):
    global num_events
    cons.add(uuid, tstamp, (user, ip, title))
    num_events += 1
    if not num_events & 1023:
        print '%d events added' % num_events

def parse(cons, fileobj):
    for line in fileobj:
        line = line.strip()
        if line.startswith('<title>'):
            title = line[7:-8]
        elif line.startswith('<timestamp>'):
            tstamp = datetime.strptime(line[11:-13], '%Y-%m-%dT%H:%M:%S')
        elif line.startswith('<username>'):
            user = line[10:-11]
            ip = ''
            uuid = hashlib.md5(user).hexdigest()
            add_event(cons, uuid, tstamp, user, ip, title)
        elif line.startswith('<ip>'):
            user = ''
            ip = line[4:-5]
            uuid = hashlib.md5(ip).hexdigest()
            add_event(cons, uuid, tstamp, user, ip, title)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: parse_wikipedia_history.py enwiki-20160501-stub-meta-history.xml.gz wikipedia-history.tdb'
        sys.exit(1)

    cons = traildb.TrailDBConstructor(sys.argv[2],
                                      ['user', 'ip', 'title'])
    parse(cons, gzip.GzipFile(sys.argv[1]))
    print 'Done adding %d events!' % num_events
    cons.finalize()
    print 'Success!'
