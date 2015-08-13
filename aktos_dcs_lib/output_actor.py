__author__ = 'aktos'


from aktos_dcs import *
import RPi.GPIO as GPIO

class GPIOOutputActor(Actor):

    def __init__(self, pin_name, pin_number, invert=False, initial=False,):
        Actor.__init__(self)
        self.pin_name = pin_name
        self.pin_number = pin_number
        self.invert = invert
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_number, GPIO.OUT)
        self.set_output(initial)
        GPIO.setwarnings(False)


    def handle_UpdateIoMessage(self, msg):
        print "notifying output status: ", self.pin_name, ": ", self.curr_state
        self.send({'IoMessage': {
            'pin_name': self.pin_name,
            'val': self.curr_state,
            'last_change': self.last_change}})

    def correct(self, input_val):
        if self.invert:
            return not bool(input_val)
        else:
            return bool(input_val)

    def handle_IoMessage(self, msg):
        msg = msg_body(msg)
        if msg['pin_name'] == self.pin_name:
            self.set_output(msg['val'])

    def set_output(self, val):
        print "OUTPUT:\tsetting output: '%s' (#%d) -> %s" % (self.pin_name, self.pin_number, str(val))
        self.curr_state = val
        self.last_change = time.time()

        GPIO.output(self.pin_number, self.correct(self.curr_state))

    def cleanup(self):
        print "GPIO cleanup..."
        try:
            GPIO.cleanup()
        except:
            pass




if __name__ == "__main__":

    ProxyActor()

    class Test(Actor):
        pass

    output_pins = {
        'piston.dir'         : 22,
    }

    for k, v in output_pins.items():
        GPIOOutputActor(pin_name=k, pin_number=v, initial=True)

    def periodic_on_off():
        print "sleeping 5s..."
        sleep(5)
        print "sleep end..."
        test = Test()
        a = 0.1
        val = True
        while True:
            test.send({'IoMessage': {'pin_name': 'piston.dir', 'val': val}})
            sleep(a)
            val = not val

    periodic_on_off()

    wait_all()
