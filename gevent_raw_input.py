__author__ = 'ceremcem'

from gevent.socket import wait_read
import sys
import gevent

def raw_input():
    wait_read(sys.stdin.fileno())
    return sys.stdin.readline()

if __name__ == "__main__":

    def naber():
        while True:
            print "naber"
            gevent.sleep(1)

    gevent.spawn(naber)
    while True:
        i = raw_input()
        print "input = " , i
        gevent.sleep(0)