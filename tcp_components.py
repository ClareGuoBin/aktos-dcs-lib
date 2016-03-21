from aktos_dcs import *
import gevent
from gevent.server import StreamServer
from gevent import (socket, Timeout)
from aktos_exceptions import SocketException


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

    def socket_write(self, data):
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


class TcpClient(object):
    def __init__(self, host='localhost', port=80, receiver=None):
        object.__init__(self)
        self.host = host
        self.port = port

        assert receiver is not None
        self.on_receive = receiver

        self.try_to_connect()
        gevent.spawn(self.socket_listener)
        gevent.spawn(self.recv_data_timeout)
        self.msg_max_age = 2  # seconds



    def socket_listener(self):
        self.chunks = []
        while True:
            try:
                data = self.client_socket.recv(2048)
                self.chunks.append(data)
                #print "socket listener got data: ", repr(data)
                if data == '':
                    raise SocketException("Disconnected, trying reconnecting...")
            except :
                self.try_to_connect()

    def try_to_connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

    def recv_data_timeout(self):
        timeout = 0.1

        prev_chunk_len = 0
        while True:
            sleep(timeout)
            if prev_chunk_len == len(self.chunks):
                # reached to timeout, print received:
                # TODO: USE LOCK HERE
                received = ''.join(self.chunks)
                self.chunks = []
                # END OF LOCK

                if received:
                    #print "RECEIVED:", repr(received)
                    self.on_receive(received)

            prev_chunk_len = len(self.chunks)

    def socket_write(self, data):
        gevent.spawn(self.__socket_send, data)

    def __socket_send(self, data):
        with Timeout(self.msg_max_age, False):
            while True:
                try:
                    self.client_socket.send(data)
                    break
                except:
                    self.try_to_connect()

    def cleanup(self):
        self.client_socket.close()


