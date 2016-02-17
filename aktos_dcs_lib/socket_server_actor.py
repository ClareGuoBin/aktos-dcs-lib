__author__ = 'ceremcem'

from aktos_dcs import *
import gevent
from gevent.server import StreamServer

class SocketHandlerActor(Actor):
    def __init__(self, socket, address):
        Actor.__init__(self)
        self.socket, self.address = socket, address
        self.is_connected = True  # TODO: set this variable somehow
        self.socket_file = socket.makefile(mode='rwb')
        self.client_id = ':'.join(map(str, self.address))
        gevent.spawn(self.socket_listener)

    def socket_listener(self):
        while self.is_connected:
            received = self.socket_file.readline()
            if not received:
                self.is_connected = False
                break
            #print "received: ", received
            self.send({'SocketServerMessage': {'data': received, 'client': self.client_id}})

    def socket_send(self, data):
        try:
            self.socket.sendall(data)
        except:
            self.is_connected = False

    def handle_SocketServerSendMessage(self, msg_raw):
        msg = get_msg_body(msg_raw)

        if msg['client'] == self.client_id or msg['client'] in ['all', 'broadcast']:
            self.socket_send(msg['data'])

    def cleanup(self):
        print "client disconnected..."
        self.socket_file.close()


class SocketServerActor(Actor):
    def __init__(self, address, port):
        Actor.__init__(self)
        self.address, self.port = address, port
        self.server = StreamServer((self.address, self.port), SocketHandlerActor) # creates a new server
        self.server.start()

if __name__ == "__main__":
    class TestSocketServerClient(Actor):
        def action(self):
            while True:
                self.send({'SocketServerSendMessage': {'data': "test socket server sending msg\n", "client": "all"}})
                sleep(2)

        def handle_SocketServerMessage(self, msg_raw):
            msg = get_msg_body(msg_raw)

            print "client sent data: ", msg["data"]

    SocketServerActor('0.0.0.0', 1234)
    TestSocketServerClient()
    wait_all()


