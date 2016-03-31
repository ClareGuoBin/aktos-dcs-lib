__author__ = 'ceremcem'

from aktos_dcs import *
import gevent 
from gevent import Timeout
import serial


class SerialPortReader(Actor):
    def __init__(self, port="/dev/ttyUSB0", baud="9600", format="8N1"):
        Actor.__init__(self)
        self.ser = serial.Serial()
        self.ser.port = "/dev/ttyUSB0"
        self.ser.baudrate = 115200
        self.ser.bytesize = 8
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        
    def prepare(self):
        self.ser.timeout = 0
        
        self.make_connection = Barrier()
        self.connection_made = Barrier()
        gevent.spawn(self.try_to_connect)
        
    def try_to_connect(self):
        
        while True:
            self.make_connection.wait()
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
                    break
                except:
                    sleep(0.1)
            print "Connected..."

    def action(self):
        print "started reading serial port..."
        print "-------------------------------"
        print self.ser

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
                        print '::' + received 

            except:
                try:
                    assert self.ser.is_open
                except:
                    self.make_connection.go()
                    self.connection_made.wait()
            
    def action_2(self):
        cmd = """import network            #0
wlan = network.WLAN(network.STA_IF)        #1
wlan.active(True)                          #2
wlan.scan()                                #3
wlan.isconnected()                         #4
wlan.connect("aea", "084DA789BF")          #5
wlan.isconnected()"""                      #6
        
        cmd_list = cmd.split("\n")
        sleep(5)
        for i in range(len(cmd_list)):
            self.ser_write(cmd_list[i]+"\r\n")
            if i == 3:
                sleep(5)
            elif i == 5:
                sleep(10)
            else:
                sleep(0.5)
                
    def ser_write(self, data):
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
                    
            

if __name__ == "__main__":
    SerialPortReader()
    wait_all()
