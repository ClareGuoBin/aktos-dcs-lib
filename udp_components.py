__author__ = 'ceremcem'
from aktos_dcs import *
from gevent.server import DatagramServer
from gevent import (socket, Timeout)
import gevent
from aktos_exceptions import SocketException


# Client components

class UdpClient(object):
    def __init__(self, host='localhost', port=80, receiver=None):
        object.__init__(self)
        self.host = host
        self.port = port

        assert receiver is not None
        self.on_receive = receiver

        self.try_to_connect()
        gevent.spawn(self.socket_listener)

    def socket_listener(self):
        self.chunks = []
        while True:
            try:
                data, address = self.client_socket.recvfrom(8192)
                print "Received: ", data, address
            except :
                print "NOT RECEIVED!!!"
                #self.try_to_connect()

    def try_to_connect(self):
        self.client_socket = socket.socket(type=socket.SOCK_DGRAM)

        i = 0
        while True:
            try:
                self.client_socket.connect((self.host, self.port))
                print "Connected..."
                break
            except:
                print "Retrying connecting..."
                gevent.sleep(i)
                i += 0.1
                max_period = 2
                i = max_period if i > max_period else i


    def socket_send(self, data):
        gevent.spawn(self.__socket_send, data)

    def __socket_send(self, data):
        with Timeout(2, False):
            while True:
                try:
                    self.client_socket.send(data)
                    break
                except:
                    print "not connected, waiting..."
                    gevent.sleep(1)

    def cleanup(self):
        self.client_socket.close()



# Server components

class UdpHandlerActor(Actor):
    def __init__(self, socket, address):
        Actor.__init__(self)
        self.socket, self.address = socket, address
        self.socket_file = socket.makefile(mode='rwb')
        self.client_id = socket.getpeername()
        gevent.spawn(self.__socket_listener__)
        self.on_connect()
        self.default_target = None

    def on_connect(self):
        print "client connected: ", self.client_id


    def __socket_listener__(self):
        while self.is_connected:
            received = self.socket_file.readline()
            if not received:
                self.is_connected = False
                break
            gevent.spawn(self.socket_read, received)
        self.kill()

    def socket_read(self, data):
        print "received: ", data


    def socket_write(self, data, target=None):
        if target is None:
            print "target is empty!"
        else:
            try:
                self.socket.sendto(data, target)
            except:
                print "didn't write to socket.."
                pass


    def cleanup(self):
        print "client %s:%s disconnected..." % self.client_id
        self.socket_file.close()


class UdpServerActor(Actor):
    def __init__(self, address="0.0.0.0", port=22334, handler=UdpHandlerActor):
        Actor.__init__(self)
        self.address, self.port = address, port
        self.server = DatagramServer((self.address, self.port), handler) # creates a new server
        self.server.serve_forever()  # this is blocker, as intended

