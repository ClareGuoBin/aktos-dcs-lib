# coding: utf-8
import gevent.monkey
gevent.monkey.patch_all()

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import smtplib
import gevent
import os

class EMail(object):
        """ Class defines method to send email
        """
        def __init__(self, debug=False, signature=""):
            self.debug = debug
            self.EMAIL_PORT = 587
            self.greenlet = None
            self.mail_signature = signature

            self.prepare_base()
            self.prepare()

            # check if class is prepared correctly
            try:
                _ = self.username
                _ = self.password
                _ = self.smtp_server
                _ = self.mail_from
            except:
                raise

        def prepare_base(self):
            pass 
        
        def prepare(self):
            """
            override this function
            :return:
            """
            pass

        def sendMessage(self, mailto, subject, msgContent, files=None):
            self.greenlet = gevent.spawn(self.__sendMessage, mailto, subject, msgContent, files)

        def __sendMessage(self, mailto, subject, msgContent, files=None):
            """ Send the email message

                Args:
                    subject(string): subject for the email
                    msgContent(string): email message Content
                    files(List): list of files to be attached
                    mailto(string): email address to be sent to
            """


            subject = make_unicode(subject)
            msgContent = make_unicode(msgContent)

            msg = self.prepareMail(mailto, subject, msgContent, files)

            # connect to server and send email
            server = smtplib.SMTP(self.smtp_server, port=self.EMAIL_PORT)
            server.ehlo()
            # use encrypted SSL mode
            server.starttls()
            # to make starttls work
            server.ehlo()
            server.login(self.username, self.password)
            server.set_debuglevel(self.debug)
            try:
                failed = server.sendmail(self.mail_from, mailto, msg.as_string())
            except Exception as er:
                print er
            finally:
                server.quit()

        def prepareMail(self, mailto, subject, msgHTML, attachments):
            """ Prepare the email to send
                Args:
                    subject(string): subject of the email.
                    msgHTML(string): HTML formatted email message Content.
                    attachments(List): list of file paths to be attached with email.
            """


            if type(mailto) == type(list()):
                mailto = ', '.join(mailto)

            msg = MIMEMultipart()
            msg['From'] = self.mail_from
            msg['To'] = mailto
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = subject

            #the Body message
            msg.attach(MIMEText(msgHTML, 'html', 'utf-8'))
            msg.attach(MIMEText(self.mail_signature, "html", 'utf-8'))
            if attachments:
                for phile in attachments:
                        # we could check for MIMETypes here
                        part = MIMEBase('application',"octet-stream")
                        part.set_payload(open(phile, "rb").read())
                        Encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(phile))
                        msg.attach(part)
            return msg


# Base class for Aktos Telemetry Subsystem Mailer
class AktosTelemetryMailBase(EMail):
    def prepare_base(self):
        self.smtp_server = 'smtp.aktos.io'
        self.mail_from = 'telemetry@aktos.io'
        self.username = "telemetry@aktos.io"

        img_html = '<img alt="aktos elektronik" src="%s" />' % "https://aktos.io/img/aktos-mail-signature-logo.png"
        self.mail_signature = "<p><a href='https://aktos.io/'>%s</a></p>" % img_html

    def prepare(self):
        self.password = "override password in your final class"



def make_unicode(input):
    if type(input) != unicode:
        input = input.decode('utf-8')
        return input
    else:
        return input

if __name__ == "__main__":
    from aktos_dcs import *
    import time


    # Test if Actors are working while mail is sending
    class TestGevent(Actor):
        def action(self):
            print "started action, ", time.time()
            while True:
                print("naber, %d" % time.time())
                sleep(0.1)


    # Example Usage:
    class TelemetryMail(AktosTelemetryMailBase):
        def prepare(self):
            self.password = "J6ctu9hgpVIfCsMDOG5SsjNKizCtXrRK85P7tCJl3k8="


    m = TelemetryMail()
    TestGevent()
    print("sending, %f" % time.time())
    m.sendMessage(["ceremcem@ceremcem.net", ""], "test-subject", "çalışöğün22", ["./cca_signal.py"])
    print("finished: %f" % time.time())
    wait_all()

