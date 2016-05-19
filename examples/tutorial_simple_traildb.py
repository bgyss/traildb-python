from traildb import TrailDBConstructor, TrailDB
from uuid import uuid4
from datetime import datetime

cons = TrailDBConstructor('tiny', ['username', 'action'])

for i in range(3):
    uuid = uuid4().hex
    username = 'user%d' % i
    for day, action in enumerate(['open', 'save', 'close']):
        cons.add(uuid, datetime(2016, i + 1, day + 1), (username, action))

cons.finalize()

for uuid, trail in TrailDB('tiny').trails():
    print uuid, list(trail)
