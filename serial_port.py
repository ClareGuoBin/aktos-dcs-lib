__author__ = 'ceremcem'

from aktos_dcs import *
from gevent_raw_input import raw_input
import gevent 
from gevent import Timeout
import serial
import sys

class SerialPortReader(Actor):
    def __init__(self, port="/dev/ttyUSB0", baud=9600, format="8N1"):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = baud
        self.ser.bytesize = int(format[0])
        self.ser.parity = format[1]
        self.ser.stopbits = int(format[2])
        self.ser.timeout = 0
        self.make_connection = Barrier()
        self.connection_made = Barrier()
        Actor.__init__(self)
        self.first_run = True
        self.last_input = None
        self.line_endings = "\r\n"
        self.read_handlers = [self.serial_read]
        self.io_prompt_started = False
        gevent.spawn(self.try_to_connect)
        gevent.spawn(self.__listener__)


    def prepare(self):
        pass

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def serial_read(self, data):
        pass

    def on_connecting(self):
        pass

    def try_to_connect(self):
        while True:
            self.make_connection.wait()
            if not self.first_run:
                gevent.spawn(self.on_disconnect)
            try:
                self.ser.close()
            except:
                pass
            connecting = None
            if not self.first_run:
                connecting = gevent.spawn(self.on_connecting)
            while True:
                try:
                    self.ser.open()
                    self.connection_made.go()
                    self.make_connection.barrier_event.clear()
                    gevent.spawn(self.on_connect)
                    try:
                        connecting.kill()
                    except:
                        pass
                    self.first_run = False
                    break
                except:
                    if connecting is None:
                        connecting = gevent.spawn(self.on_connecting)

                    sleep(0.1)

    def __listener__(self):
        str_list = []
        while True:
            try:
                sleep(0.01) # amount of time between packages
                nextchar = self.ser.read(self.ser.inWaiting())
                if nextchar:
                    str_list.append(nextchar)
                else:
                    if len(str_list) > 0:
                        received = ''.join(str_list)
                        str_list = []
                        
                        # use received data
                        #print "DEBUG: RECEIVED: ", repr(received)
                        for i in self.read_handlers:
                            gevent.spawn(i, received)

            except:
                try:
                    assert self.ser.is_open
                except:
                    self.make_connection.go()
                    self.connection_made.wait()

    def add_read_handler(self, handler):
        self.read_handlers.append(handler)

    def send_cmd(self, cmd, s=0.0):
        self.serial_write(cmd + self.line_endings)
        sleep(s)

    def serial_write(self, data):
        with Timeout(1, False):
            while True:
                try:
                    self.ser.write(data)
                    break
                except:
                    try:
                        assert self.ser.is_open
                    except:
                        self.make_connection.go()
                        self.connection_made.wait()

    def start_io_prompt(self):
        if not self.io_prompt_started:
            self.io_prompt_started = True
            self.add_read_handler(self.prompt_read)
            gevent.spawn(self.prompt_write)
        else:
            print "WARNING: Prompt already started..."



    def prompt_read(self, data):
        echo_index = 0
        if self.last_input is not None:
            if self.last_input[-1] == "\n":
                self.last_input = self.last_input[:-1]  # remove \n char

            echo_index = data.find(self.last_input)
            if echo_index > -1:
                echo_index += len(self.last_input)
                echo_index += len(self.line_endings)  # remove \r\n at the end
            self.last_input = None
        clear_data = data[echo_index:]
        sys.stdout.write(clear_data)
        sys.stdout.flush()

    def prompt_write(self):
        while True:
            self.last_input = raw_input()
            stripped = self.last_input[:-1]  # remove "\n" at the end
            self.send_cmd(stripped)

    def cleanup(self):
        try:
            self.ser.close()
        except:
            pass
