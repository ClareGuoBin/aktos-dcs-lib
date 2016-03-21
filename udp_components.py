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


    def socket_write(self, data):
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




class UdpServerActor(Actor):
    def __init__(self, address="0.0.0.0", port=22334):
        Actor.__init__(self)
        self.address, self.port = address, port
        self.server = DatagramServer((self.address, self.port), self.socket_read) # creates a new server
        gevent.spawn(self.server.serve_forever)

    def socket_read(self, data, address):
        print "server actor received", data, address
        print "server makes echo: "
        self.socket_write(data, address)

    def socket_write(self, data, target=None):
        if target is None:
            print "target is empty!"
        else:
            try:
                self.server.sendto(data, target)
            except Exception as e:
                print "didn't write to socket..", e
                pass

