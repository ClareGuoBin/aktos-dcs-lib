__author__ = 'aktos'


from aktos_dcs import *

class GPIOOutputActor(Actor):

    def __init__(self, pin_name, pin_number, invert=False, initial=False,):
        import RPi.GPIO as GPIO
        self.GPIO = GPIO
        Actor.__init__(self)
        self.pin_name = pin_name
        self.pin_number = pin_number
        self.invert = invert
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.pin_number, self.GPIO.OUT)
        self.set_output(initial)
        self.GPIO.setwarnings(False)


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

        self.GPIO.output(self.pin_number, self.correct(self.curr_state))

    def cleanup(self):
        """
        print "GPIO cleanup..."
        try:
            self.GPIO.cleanup()
        except:
            pass
        """
        self.GPIO.output(self.pin_number, False)
        self.GPIO.setup(self.pin_number, self.GPIO.IN)
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
