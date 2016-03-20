__author__ = 'ceremcem'

from aktos_dcs import *
from gevent import (socket, Timeout)
import gevent


class SocketException(Exception):
    pass


class SocketClient(object):
    def __init__(self, host='localhost', port=80, receiver=None):
        object.__init__(self)
        self.host = host
        self.port = port

        assert receiver is not None
        self.on_receive = receiver

        self.try_to_connect()
        gevent.spawn(self.socket_listener)
        gevent.spawn(self.recv_data_timeout)


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

    def socket_send(self, data):
        self.client_socket.send(data)

    def cleanup(self):
        self.client_socket.close()


class SocketClientActor(Actor):
    def __init__(self, host='localhost', port=80):
        Actor.__init__(self)
        self.host = host
        self.port = port
        self.socket_client = SocketClient(host, port, self.broadcast_data)

    def broadcast_data(self, data):
        self.send_SocketMessage(host=self.host, port=self.port, data=data)

    def handle_SocketMessage(self, msg):
        self.socket_client.socket_send(pack(msg))

if __name__ == "__main__":
    def handler(data):
        print "naber", data

    x = SocketClient(host="localhost", port=11223, receiver=handler)

    wait_all()

