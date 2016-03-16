# coding: utf-8
import gevent.monkey
gevent.monkey.patch_all()

import imaplib
import gevent
import os
from aktos_dcs.unicode_tools import *
import email
import email.header
import datetime

class EMail(object):
        """ Class defines method to send email
        """
        def __init__(self, debug=False, signature=""):
            self.debug = debug
            self.greenlet = None
            self.mail_signature = signature

            self.prepare_base()
            self.prepare()

            # check if class is prepared correctly
            try:
                _ = self.username
                _ = self.password
                _ = self.imap_server
                _ = self.imap_port
            except:
                raise

            try:
                _ = self.imap_port
            except:
                self.imap_port = 143

            self.mailbox = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mailbox.login(self.username, self.password)

        def prepare_base(self):
            pass 
        
        def prepare(self):
            """
            override this function
            :return:
            """
            pass



# Base class for Aktos Telemetry Subsystem Mailer
class AktosTelemetryMailBase(EMail):
    def prepare_base(self):
        self.imap_server = 'imap.aktos.io'
        self.mail_from = 'telemetry@aktos.io'
        self.username = "telemetry@aktos.io"

        img_html = '<img alt="aktos elektronik" src="%s" />' % "https://aktos.io/img/aktos-mail-signature-logo.png"
        self.mail_signature = "<p><a href='https://aktos.io/'>%s</a></p>" % img_html

    def prepare(self):
        self.password = "override password in your final class"




if __name__ == "__main__":
    from aktos_dcs import *
    import time

    # Test if Actors are working while mail is sending
    class TestGevent(Actor):
        def action(self):
            print "Test code is started action, ", time.time()
            while True:
                print("naber, %d" % time.time())
                sleep(0.1)

    #TestGevent()


    # Example Usage:
    class TelemetryMail(AktosTelemetryMailBase):
        def prepare(self):
            self.password = "r1D84N9HxSdzv0Hrx29k1OUY2NnvjJFBpkX0XNxONto="
            self.imap_server = 'imappro.zoho.com'
            self.imap_port = 993
            self.mail_from = 'telemetry@aktos-elektronik.com'
            self.username = "telemetry@aktos-elektronik.com"


    m = TelemetryMail()
    resp, rec = m.mailbox.select("inbox")
    if resp == "OK":
        for num in rec[0].split():
            rv, data = m.mailbox.fetch(num, '(RFC822)')
            if rv != 'OK':
                print "ERROR getting message", num
                break

            msg = email.message_from_string(data[0][1])
            decode = email.header.decode_header(msg['Subject'])[0]
            subject = make_unicode(decode[0])
            print 'Message %s: %s' % (num, subject)
            print 'Raw Date:', msg['Date']
            # Now convert to local date-time
            date_tuple = email.utils.parsedate_tz(msg['Date'])
            if date_tuple:
                local_date = datetime.datetime.fromtimestamp(
                    email.utils.mktime_tz(date_tuple))
                print "Local Date:", \
                    local_date.strftime("%a, %d %b %Y %H:%M:%S")
            print "Msg from:", msg['from']

            if msg.get_content_maintype() == 'multipart': #If message is multi part we only want the text version of the body, this walks the message and gets the body.
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True)
                    else:
                        continue
                    print body

    print("finished: %f" % time.time())
    wait_all()

