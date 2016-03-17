#coding: utf-8
__author__ = 'ceremcem'

from aktos_dcs import *
from aktos_email import EMail
import gevent

class EMailActor(EMail, Actor):
    def __init__(self):
        EMail.__init__(self)

        # WORKAROUND
        # prevent self.prepare run by both EMail and Actor
        x = self.prepare
        def _():
            pass
        self.prepare = _
        # END OF WORKAROUND

        Actor.__init__(self)

        self.poll_period = 2  # seconds
        self.last_mail_index = -1

        gevent.spawn(self.poller)

    def poller(self):
        while True:

            mail_index = self.get_last_mail_index()
            if self.last_mail_index < mail_index:
                mail = self.get_mail(mail_index)
                if mail["from"] is not None:
                    self.last_mail_index = mail["index"]
                    gevent.spawn(self.handle_EMail, mail)
            sleep(self.poll_period)

    def handle_EMail(self, mail):
        pass

class TelemetryMailActorBase(EMailActor):
    def prepare_base(self):
        self.username = "telemetry@aktos-elektronik.com"
        self.mail_from = 'telemetry@aktos-elektronik.com'
        self.imap_server = 'imappro.zoho.com'
        self.imap_port = 993
        self.smtp_server = "smtp.zoho.com"
        self.smtp_port = 587
        self.mail_signature = """
            <p>
                <a href='https://aktos.io/'>
                    <img alt="aktos elektronik"
                        src="https://aktos.io/img/aktos-mail-signature-logo.png" />
                </a>
            </p>
            """


if __name__ == "__main__":

    class TelemetryMailActor(TelemetryMailActorBase):
        def prepare(self):
            print "Prepare is run!"
            self.password = "r1D84N9HxSdzv0Hrx29k1OUY2NnvjJFBpkX0XNxONto="

        def action(self):
            i = 0
            print "Periodic sending mail will be started in 60 seconds..."
            while True:
                sleep(60)
                print "Sending mail number: %d..." % i

                recipients = ["ceremcem@ceremcem.net", self.username]
                subject = "test-subject-çalışöğün-number: %d" % i
                content = "çalışöğün22, seq: %d" % i
                attachments = ["./cca_signal.py"]
                self.send_mail(recipients, subject, content, attachments)
                i += 1

        def handle_EMail(self, mail):
            print "Got mail: "
            print "Index: ", mail["index"]
            print "From: ", mail["from"]
            print "To: ", mail["to"]
            print "Timestamp: ", mail["unix_timestamp"]
            print "Subject: ", mail["subject"]
            print "Body: ", mail["body"]

            print "This mail is received by inbox %d seconds ago." % (time.time() -
                                                                      mail["unix_timestamp"])



    TelemetryMailActor()
    wait_all()

