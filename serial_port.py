__author__ = 'ceremcem'

from aktos_dcs import *
from io_prompt import IoPrompt
import gevent
from gevent import Timeout
import serial


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
        self.line_endings = "\r\n"
        self.read_handlers = [self.serial_read]
        self.first_run = True
        self.additional_greenlets = []

        Actor.__init__(self)
        self.additional_greenlets.append(gevent.spawn(self.try_to_connect))
        self.additional_greenlets.append(gevent.spawn(self.__listener__))


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
        """
        listens for incoming data.
        calls the callback when EOL character is received or
        nothing more received after frame_interval delay.
        :return:
        """
        frame_interval = 0.1
        str_list = []
        while True:
            try:
                with Timeout(frame_interval):
                    while True:
                        c = self.ser.read()
                        str_list.append(c)
                        if c == "\n" or c == '':
                            break
                received = ''.join(str_list)
                str_list = []
                if received:
                    for i in self.read_handlers:
                        gevent.spawn(i, received)
            except IOError:
                self.ser.close()
            except:
                try:
                    assert self.ser.is_open
                except:
                    self.make_connection.go()
                    self.connection_made.wait()

            sleep(0.001)

    def add_read_handler(self, handler):
        self.read_handlers.append(handler)

    def send_cmd(self, cmd, s=0.0):
        _ = cmd + self.line_endings
        #print "DEBUG: SENDING CMD: ", repr(_)
        self.serial_write(_)
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
        self.io_prompt = IoPrompt()
        self.io_prompt.send_cmd = self.send_cmd
        self.read_handlers.append(self.io_prompt.prompt_read)
        self.io_prompt.start_io_prompt()


    def cleanup(self):
        for i in self.additional_greenlets:
            try:
                i.kill()
            except:
                pass

        self.io_prompt.kill()
        try:
            self.ser.close()
        except:
            pass
