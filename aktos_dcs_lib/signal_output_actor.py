__author__ = 'aktos'
from gevent import monkey
monkey.patch_all()

from aktos_dcs import *
from output_actor import *


from gevent.subprocess import Popen, PIPE, call
import gevent
import signal
import os

import inspect

class ServoActor(Actor):
    """
    TODO: after a timeout, disable motor

    sends signal to another application

    signal.SIGCONT : Start square wave
    signal.SIGUSR2 : Stop square wave
    signal.SIGUSR1 : Heartbeat
    """

    def __init__(self, device_name, invert=False, pins={}):
        self.__is_started = False

        Actor.__init__(self)

        self.pul = "%s.pul" % device_name
        self.enab = "%s.enab" % device_name
        self.dir = "%s.dir" % device_name
        GPIOOutputActor(pin_name=self.enab, pin_number=pins['enab'])
        GPIOOutputActor(pin_name=self.dir, pin_number=pins['dir'])

        self.device_name = device_name

        self.START = signal.SIGCONT
        self.STOP = signal.SIGUSR2
        self.HB = signal.SIGUSR1

        self.run_heartbeat = True

        self.file_dir = cmd_subfolder = os.path.realpath(
            os.path.abspath(
                os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0],".")))

        self.start_driver()
        self.wait_started()

    def start_driver(self):
        while True:
            try:
                try:
                    call(['rm', '/var/run/pigpio.pid'])
                except Exception, e:
                    pass

                self.cleanup()


                self.driver_name = 'swave2'
                swave_path = os.path.join(self.file_dir, self.driver_name)
                print "swave executable: ", swave_path
                self.swave = Popen([swave_path])
                sleep(1) # change this line with "as soon as started"
                self.send_signal(self.HB)
                self.run_heartbeat = True
                gevent.spawn(self.send_heartbeat)
                break
            except:
                pass

        self.__is_started = True

    def wait_started(self):
        while not self.__is_started:
            sleep(0.01)

    def handle_ServoMessage(self, msg):
        print "servo got message: ", msg['msg_id']
        msg = msg_body(msg)
        if msg['cmd'] == 'forward':
            print "%s moving forward..." % self.device_name
            self.set_dir(True)
            self.start_sw()
        elif msg['cmd'] == 'backwards':
            print "%s moving backwards..." % self.device_name
            self.set_dir(False)
            self.start_sw()
        elif msg['cmd'] == 'stop':
            print "%s stopping..." % self.device_name
            self.stop_sw()

    def set_enab(self, b=False):
        self.send({'IoMessage': {'pin_name': self.enab, 'val': b}})

    def set_dir(self, b=False):
        self.send({'IoMessage': {'pin_name': self.dir, 'val': b}})

    def start_sw(self):
        self.set_enab(True)
        self.send_signal(self.START)

    def stop_sw(self):
        self.send_signal(self.STOP)
        self.set_enab(False)

    def send_heartbeat(self):
        while self.run_heartbeat:
            self.send_signal(self.HB)
            sleep(0.3)

    def send_signal(self, signal):
        #os.kill(self.swave_pid, signal)
        self.swave.send_signal(signal)

    def cleanup(self):
        print "cleaning up ServoActor..."
        try:
            self.run_heartbeat = False
            call(['killall', self.driver_name])
            print "killed successfully..."
        except Exception, e:
            print "error killing driver program..."


if __name__ == "__main__":
    class Test(Actor):
        pass
    # -------------------------------------------------

    #ProxyActor()
    piston_pins = {
        'pul'         : 4,
        'dir'         : 22,
        'enab'        : 17,
    }
    ServoActor(device_name="piston", pins=piston_pins).wait_started()

    t = Test()

    while True:
        t.send({'ServoMessage': {'cmd': "forward"}})
        sleep(2)
        t.send({'ServoMessage': {'cmd': "backwards"}})
        sleep(2)
        t.send({'ServoMessage': {'cmd': "stop"}})
        sleep(2)

    wait_all()
