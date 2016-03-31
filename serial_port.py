__author__ = 'ceremcem'

from aktos_dcs import *
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
        Actor.__init__(self)
        gevent.spawn(self.try_to_connect)

    def prepare(self):
        pass

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def serial_read(self, data):
        pass

    def try_to_connect(self):
        while True:
            self.make_connection.wait()
            gevent.spawn(self.on_disconnect)
            try:
                self.ser.close()
            except:
                pass
            print "Trying to connect..."
            while True:
                try:
                    self.ser.open()
                    self.connection_made.go()
                    self.make_connection.barrier_event.clear()
                    gevent.spawn(self.on_connect)
                    break
                except:
                    sleep(0.1)

    def action(self):
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
                        gevent.spawn(self.serial_read, received)
            except:
                try:
                    assert self.ser.is_open
                except:
                    self.make_connection.go()
                    self.connection_made.wait()

    def ser_write(self, data):
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

    def cleanup(self):
        try:
            self.ser.close()
        except:
            pass
