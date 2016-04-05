__author__ = 'ceremcem'

from aktos_dcs import Actor
from gevent_raw_input import raw_input
import sys
import gevent


class IoPrompt(Actor):
    def prepare(self):
        self.last_input = None
        self.io_prompt_started = False
        self.send_cmd = None
        self.additional_greenlets = []
        self.cancel_echo = True

    def start_io_prompt(self):
        assert self.send_cmd is not None
        if not self.io_prompt_started:
            self.io_prompt_started = True
            #self.add_read_handler(self.prompt_read)
            self.additional_greenlets.append(gevent.spawn(self.prompt_write))
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
            else:
                echo_index = 0
            self.last_input = None

        if self.cancel_echo:
            clear_data = data[echo_index:]
            # remove any preceding line endings
            for i in range(2):
                if len(clear_data) > 0:
                    if clear_data[0] in ["\n", "\r"]:
                        clear_data = clear_data[1:]

            sys.stdout.write(clear_data)
        else:
            sys.stdout.write(data)

        sys.stdout.flush()

    def prompt_write(self):
        while True:
            self.last_input = raw_input()
            stripped = self.last_input[:-1]  # remove "\n" at the end
            self.send_cmd(stripped)

    def cleanup(self):
        for i in self.additional_greenlets:
            try:
                i.kill()
            except:
                pass
