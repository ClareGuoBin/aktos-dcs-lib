__author__ = 'aktos'


from aktos_dcs import *

class VirtualIoActor(Actor):

    def __init__(self, pin_name, pin_number=None, initial=False,):
        Actor.__init__(self)
        self.pin_name = pin_name
        self.pin_number = pin_number
        self.set_output(initial)


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
        msg = get_msg_body(msg)
        if msg['pin_name'] == self.pin_name:
            self.set_output(msg['val'])

    def set_output(self, val):
        print "Virtual IO:\tsetting: '%s' -> %s" % (self.pin_name, str(val))
        self.curr_state = val
        self.last_change = time.time()



if __name__ == "__main__":
    pass
