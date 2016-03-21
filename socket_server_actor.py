__author__ = 'ceremcem'

from aktos_dcs import *
import gevent
from gevent.server import StreamServer
from gevent.server import DatagramServer



class TcpHandlerActor(Actor):
    def __init__(self, socket, address):
        Actor.__init__(self)
        self.socket, self.address = socket, address
        self.is_connected = True
        self.socket_file = socket.makefile(mode='rwb')
        self.client_id = socket.getpeername()
        gevent.spawn(self.__socket_listener__)
        self.on_connect()

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


    def socket_send(self, data):
        try:
            self.socket.sendall(data)
        except:
            self.is_connected = False
            self.kill()


    def cleanup(self):
        print "client %s:%s disconnected..." % self.client_id
        self.socket_file.close()


class TcpServerActor(Actor):
    def __init__(self, address="0.0.0.0", port=22334, handler=TcpHandlerActor):
        Actor.__init__(self)
        self.address, self.port = address, port
        self.server = StreamServer((self.address, self.port), handler) # creates a new server
        self.server.start()  # this is blocker, as intended


class UdpServer(DatagramServer):

    def handle(self, data, address): # pylint:disable=method-hidden
        print('%s: got %r' % (address[0], data))
        self.socket.sendto(('Received %s bytes' % len(data)).encode('utf-8'), address)

