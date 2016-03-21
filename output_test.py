__author__ = 'aktos'

import gevent
import time

sleep = gevent.sleep

import simplejson as json

from gevent.queue import Queue
from aktos_dcs.Messages import *
import msgpack
from uuid import uuid4
import libuuid

q = Queue()

def my_print_func(got):
    print "here is what I got: ", msgpack.unpackb(got[0]), time.time() - got[1]

def subscriber():
    try:
        while True:
            got = q.get()
            #print "here is what I got: ", got[0], time.time() - got[1]
            my_print_func( got)
    except:
        import pdb
        pdb.set_trace()

gevent.spawn(subscriber)

# libuuid: %52.5; uuid: %57.5; without them: %52.2
# simplejson: %52.2; python dict: %46
# directly print: %46, gevent.spawn for every message: %50, direct calling: %46
# without packing: %46; msgpack.packb: %50
# msgpack normal dict: %50; msgpack Message class: %60, envelp: %48.5

def envelp(message):
    return {
        'sender': [],
        'timestamp': time.time(),
        'msg_id': '', # {{.actor_id}}.{{.prev_msg_id + 1}}
        'payload': message,
    }

val = True
while True:
    print "piston.dir: ", val
    send = "piston.dir: " \
           "" + str(val)
    q.put([msgpack.packb(envelp({'send': send})), time.time()])
    val = not val
    sleep(0.001)