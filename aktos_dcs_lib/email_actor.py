#coding: utf-8
__author__ = 'ceremcem'

from aktos_dcs import *
import gevent


class EMailActorException(Exception):
    pass


class EMailActor(Actor):
    def __init__(self):
        self.mail_client = None
        Actor.__init__(self)

        try:
            assert self.mail_client is not None
        except:
            raise EMailActorException("mail_client should be defined in prepare method!")
            self.kill()

        self.poll_period = 2  # seconds
        self.last_mail_index = -1

        gevent.spawn(self.__poller__)
        self.send_mail = self.mail_client.send_mail

    def __poller__(self):
        while True:

            mail_index = self.mail_client.get_last_mail_index()

            if self.last_mail_index < 0:
                # actor started just now, take it as a reference point
                self.last_mail_index = mail_index
                
            if self.last_mail_index < mail_index:
                mail = self.mail_client.get_mail(mail_index)
                if mail["from"] is not None:
                    self.last_mail_index = mail["index"]
                    gevent.spawn(self.handle_EMail, mail)
            sleep(self.poll_period)

    def handle_EMail(self, mail):
        pass


