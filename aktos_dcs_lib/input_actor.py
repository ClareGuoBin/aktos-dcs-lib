__author__ = 'aktos'

from aktos_dcs import *

class GPIOInputActor(Actor):

    def __init__(self, pin_name, pin_number, invert=False, pull_up_down="pull_up"):
        import RPi.GPIO as GPIO
        self.GPIO = GPIO
        Actor.__init__(self)
        self.pin_name = pin_name
        self.pin_number = pin_number
        self.invert = invert
        print "initializing ", self.pin_name, " (", self.pin_number, ")"
        self.GPIO.setmode(self.GPIO.BCM)

        p = self.GPIO.PUD_UP
        if pull_up_down != "pull_up":
            p = self.GPIO.PUD_DOWN

        self.GPIO.setup(self.pin_number, self.GPIO.IN, pull_up_down=p)
        self.last_change = -1
        self.curr_state = 0
        self.prev_state = 0

        self.GPIO.setwarnings(False)

        self.GPIO.add_event_detect(self.pin_number, self.GPIO.BOTH, callback=self.gpio_callback)

    def handle_UpdateIoMessage(self, msg):
        print "notifying input status: ", self.pin_name, ": ", self.curr_state
        self.broadcast_status()

    def correct(self, input_val):
        if self.invert:
            return not bool(input_val)
        else:
            return bool(input_val)

    def broadcast_status(self):
        self.send({'IoMessage': {
                'pin_name': self.pin_name,
                'val': self.curr_state,
                'last_change': self.last_change}})

    def gpio_callback(self, channel):
        if channel == self.pin_number:
            self.poll_gpio()

    def poll_gpio(self):
        self.curr_state = self.correct(self.GPIO.input(self.pin_number))

        if self.curr_state != self.prev_state:
            edge = ""
            if not self.prev_state and self.curr_state:
                edge = "rising_edge"
            else:
                #if self.prev_state == inv_high and self.curr_state == inv_low:
                edge = "falling_edge"

            self.prev_state = self.curr_state
            self.last_change = time.time()

            print "INPUT:\tchanged state: ", self.pin_name, " -> ", edge
            self.broadcast_status()
            return True
        return False

    def action(self):
        sleep(1)
        while self.running:
            if self.poll_gpio():
                print
                print "***************************** THIS IS A BIG PROBLEM IN INPUT_ACTOR! REPORT THIS!"
                print
            sleep(0.5) # TODO: this is too long!

    def cleanup(self):
        """
        print "GPIO cleanup..."
        try:
            self.GPIO.cleanup()
        except:
            pass
        """
        pass

if __name__ == "__main__":

    #ProxyActor()

    class Test(Actor):
        def handle_IoMessage(self, msg):
            msg = get_msg_body(msg)
            print "Test got IoMessage: ", msg



    input_pins = {
        'fully-opened'  : 24,
        'fully-closed'  : 23,
        'move-forward'  : 8,
        'move-backward' : 27,
    }

    for k, v in input_pins.items():
        GPIOInputActor(pin_name=k, pin_number=v, invert=True)

    test = Test()
    while True:
        print "requesting io update..."
        test.send({'UpdateIoMessage': {}})
        sleep(5)

    wait_all()
