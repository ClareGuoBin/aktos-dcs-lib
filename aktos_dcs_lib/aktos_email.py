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
        def __init__(self, mailFrom, server, usrname, password, debug=False, signature=""):
            self.debug = debug
            self.mailFrom = mailFrom
            self.smtpserver = server
            self.EMAIL_PORT = 587
            self.usrname = usrname
            self.password = password
            self.greenlet = None
            self.mail_signature = signature

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
            #msgContent = make_unicode(msgContent)

            msg = self.prepareMail(mailto, subject, msgContent, files)

            # connect to server and send email
            server=smtplib.SMTP(self.smtpserver, port=self.EMAIL_PORT)
            server.ehlo()
            # use encrypted SSL mode
            server.starttls()
            # to make starttls work
            server.ehlo()
            server.login(self.usrname, self.password)
            server.set_debuglevel(self.debug)
            try:
                failed = server.sendmail(self.mailFrom, mailto, msg.as_string())
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
            msg['From'] = self.mailFrom
            msg['To'] = mailto
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = subject

            #the Body message
            msg.attach(MIMEText(msgHTML, 'html'))
            msg.attach(MIMEText(self.mail_signature, "html"))
            if attachments:
                for phile in attachments:
                        # we could check for MIMETypes here
                        part = MIMEBase('application',"octet-stream")
                        part.set_payload(open(phile, "rb").read())
                        Encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(phile))
                        msg.attach(part)
            return msg

class AktosTelemetryMailBase(EMail):
    def __init__(self, passwd):
        SMTPserver      = 'smtp.aktos.io'
        sender          = 'telemetry@aktos.io'
        USERNAME        = "telemetry@aktos.io"
        PASSWORD        = passwd

        img_html = '<img alt="aktos elektronik" src="%s" />' % "https://aktos.io/img/aktos-mail-signature-logo.png"
        mail_signature = "<p><a href='https://aktos.io/'>%s</a></p>" % img_html

        EMail.__init__(self,
                       mailFrom=sender,
                       server=SMTPserver,
                       usrname=USERNAME,
                       password=PASSWORD,
                       signature=mail_signature)

        """
        use instance of this class like this:

            mail = AktosTelemetryMail()

            recipients = ["ceremcem@ceremcem.net", "user@example.com"]
            subject = "my test subject"
            contents = "my test contents"
            files = ["./path/to/file", "/path/to/another/file"]
            mail.sendMessage(recipients, subject, contents, files)

        """

def make_unicode(input):
    if type(input) != unicode:
        input = input.decode('utf-8')
        return input
    else:
        return input

if __name__ == "__main__":
    from aktos_dcs import *
    import time

    class TelemetryMail(AktosTelemetryMailBase):
        def __init__(self):
            passwd = "MB+L31oKtqsNNYjjSCxzd61cHKuRJrL76oNUtOQMutE="
            AktosTelemetryMailBase.__init__(self, passwd)



    class TestGevent(Actor):
        def action(self):
            print "started action, ", time.time()
            while True:
                print("naber, %d" % time.time())
                sleep(0.1)


    m = TelemetryMail()
    TestGevent()
    print("sending, %f" % time.time())
    m.sendMessage(["ceremcem@ceremcem.net", ""], "test-subject", "çalışöğün22", ["./cca_signal.py"])
    print("finished: %f" % time.time())
    wait_all()

