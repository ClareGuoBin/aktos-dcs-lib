__author__ = 'ceremcem'

from aktos_dcs import *
from gevent import (socket, Timeout)
import gevent

class SocketClientActor(Actor):
    def __init__(self, host='localhost', port=80):
        Actor.__init__(self)
        self.host = host
        self.port = port

    def action(self):
        self.try_to_connect()
        gevent.spawn(self.socket_listener)
        gevent.spawn(self.recv_data_timeout)

    def socket_listener(self):
        self.chunks = []
        while 1:
            try:
                with Timeout(5, Exception):
                    data = self.client_socket.recv(2048)
                    self.chunks.append(data)
                    #print "socket listener got data: ", data
            except:
                self.try_to_connect()

    def try_to_connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.client_socket.connect((self.host, self.port))
                print "Connected..."
                break
            except:
                print "Retrying connecting..."
                sleep(2)

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
                    print "RECEIVED:", received
                    self.send({'SocketClientMessage': {'data': received}})

            prev_chunk_len = len(self.chunks)

    def socket_send(self, data):
        self.client_socket.send(data)

    def cleanup(self):
        self.client_socket.close()

if __name__ == "__main__":
    class Test(Actor):
        def handle_SocketClientMessage(self, msg_raw):
            msg = get_msg_body(msg_raw)

            print "Test actor got msg: ", msg['data']

    class TestIo(Actor):
        def handle_SocketClientMessage(self, msg_raw):
            msg = get_msg_body(msg_raw)

            val = msg["data"].split()[-1]
            val_norm = int(val) / 100
            print "resending value: ", val_norm
            self.send({'IoMessage': {'pin_name': 'vpin-2', 'val': val_norm}})
            self.send({'IoMessage': {'pin_name': 'terazi-1', 'val': int(val)}})

    print "Starting raw socket reader test..."
    print "start a raw server with 'nc -l 1234' command in bash "
    ProxyActor()
    SocketClientActor(host="localhost", port=1234)
    Test()
    #TestIo()
    wait_all()
