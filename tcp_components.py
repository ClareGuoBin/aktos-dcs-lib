from aktos_dcs import *
import gevent
from gevent.server import StreamServer
from gevent import (socket, Timeout)
from aktos_exceptions import SocketException
from gevent.queue import Queue
import struct
from gevent import GreenletExit

import traceback

class TcpHandlerActor(Actor):
    def __init__(self, socket, address):
        Actor.__init__(self)
        try:
            self.line_ending = "\n"
            self.socket, self.address = socket, address
            self.socket_file = self.socket.makefile(mode='rwb')
            self.client_id = self.socket.getpeername()
            self.__listener_g__ = gevent.spawn(self.__socket_listener__)
            self.on_connect()
        except:
            print "PROBLEM ON INIT!!!"
            traceback.print_exc()
            raise

    def on_connect(self):
        print "client connected: ", self.client_id

    def on_disconnect(self):
        print "client disconnected: ", self.client_id

    def __socket_listener__(self):
        while True:
            with Timeout(0.01, False):
                received_buff = ''
                received = None
                while True:
                    received = self.socket_file.read(1)
                    if received == '':
                        # Connection seems to be closed
                        self.kill()
                    elif received:
                        received_buff += received
                    if len(self.line_ending) > 0:
                        if received == self.line_ending:
                            # equivalent to "readline()"
                            break
            if len(received_buff) > 0:
                gevent.spawn(self.socket_read, received_buff)

    def socket_read(self, data):
        print "received: ", data

    def socket_write(self, data):
        try:
            self.socket_file.write(data)
            self.socket_file.flush()
        except:
            # Debug
            #traceback.print_exc()
            self.kill()

    def cleanup(self):
        self.on_disconnect()
        try:
            self.__listener_g__.kill()
        except GreenletExit:
            pass

        self.socket_file.close()
	self.socket.shutdown(socket.SHUT_RDWR)
	self.socket.close()

class TcpServerActor(Actor):
    def __init__(self, address="0.0.0.0", port=22334, handler=TcpHandlerActor):
        Actor.__init__(self)
        self.address, self.port = address, port
        self.server = StreamServer((self.address, self.port), handler) # creates a new server
        gevent.spawn(self.server.serve_forever)


# LastStableIsImportant
#   PreviousIsUseless
#   PreviousIsGoodToKnow
#   PreviousIsMandatory

class TcpClient(object):
    def __init__(self, host='localhost', port=80, receiver=None):
        object.__init__(self)
        self.host = host
        self.port = port

        assert receiver is not None
        self.on_receive = receiver

        #self.try_to_connect()
        gevent.spawn(self.socket_listener)
        gevent.spawn(self.recv_data_timeout)
        self.msg_max_age = 2  # seconds
        self.send_queue = Queue()
        gevent.spawn(self.__send_queue_worker__)

        self.line_ending = "\n"




    def socket_listener(self):
        self.chunks = []
        while True:
            try:
                data = self.client_socket.recv(2048)
                #print "socket listener got data: ", repr(data)
                if data == '':
                    raise SocketException("Disconnected, trying reconnecting...")
                else:
                    self.chunks.append(data)
            except:
                self.try_to_connect()

    def try_to_connect(self):
        print "Trying to connect"
        # use a new socket when attempting to reconnect!
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        i = 2
        while True:
            try:
                a = self.client_socket.connect((self.host, self.port))
                print "Connected...", a
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
        self.send_queue.put((data, time.time()))

    def __send_queue_worker__(self):
        while True:
            data, timestamp = self.send_queue.get()
            while timestamp + self.msg_max_age > time.time():
                try:
                    print "sending following data: ", repr(data)
                    self.client_socket.send(data, timeout=0)
                    if self.line_ending:
                        print "here is a line ending: ", repr(self.line_ending)
                        # Append a line ending if there is none found:
                        if data[-len(self.line_ending)] != self.line_ending:
                            self.client_socket.send(self.line_ending, timeout=0)
                    break
                except:
                    self.try_to_connect()


    def cleanup(self):
        self.client_socket.close()


