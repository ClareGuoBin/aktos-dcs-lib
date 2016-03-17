# coding: utf-8
import gevent.monkey
gevent.monkey.patch_all()

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import smtplib
import imaplib
import gevent
from aktos_dcs.unicode_tools import *
import email
import email.header
import os
from aktos_dcs import Barrier
import time

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
                _ = self.smtp_server
                _ = self.imap_server
            except:
                raise


            # set defaults
            try:
                _ = self.imap_port
            except:
                self.imap_port = 143

            try:
                _ = self.smtp_port
            except:
                self.smtp_port = 587

            try:
                _ = self.mail_from
            except:
                self.mail_from = self.username

            self.mailbox = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.smtp_session = None

            # alias
            self.send_mail = self.sendMessage

            # login in background
            self.login_ok = False
            self.login_barrier = Barrier()

            gevent.spawn(self.login)


        def prepare_base(self):
            pass 
        
        def prepare(self):
            """
            override this function
            :return:
            """
            pass


        def login(self):
            self.mailbox.login(self.username, self.password)

            server = smtplib.SMTP(self.smtp_server, port=self.smtp_port)
            server.ehlo()
            # use encrypted SSL mode
            server.starttls()
            # to make starttls work
            server.ehlo()
            server.login(self.username, self.password)
            server.set_debuglevel(self.debug)

            self.smtp_session = server
            self.login_ok = True
            self.login_barrier.go()

        def quit(self):
            self.smtp_session.quit()
            self.mailbox.close()
            self.mailbox.logout()


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
            if not self.login_ok:
                #print "WARNING: Not logged in yet, waiting for log in", time.time()
                self.login_barrier.wait()
                #print "INFO: Logged in, continuing sending message...", time.time()


            subject = make_unicode(subject)
            msgContent = make_unicode(msgContent)

            msg = self.prepareMail(mailto, subject, msgContent, files)

            # connect to server and send email
            try:
                failed = self.smtp_session.sendmail(self.mail_from, mailto, msg.as_string())
            except Exception as er:
                print er

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

        def get_last_mail_index(self):
            if not self.login_ok:
                #print "WARNING: Not logged in yet, waiting for log in", time.time()
                self.login_barrier.wait()
                #print "INFO: Logged in, continuing getting message...", time.time()

            resp, received_list = self.mailbox.select("inbox")
            if resp == "OK":
                last_msg_num = received_list[0].split()[-1]
            else:
                last_msg_num = None
            return last_msg_num


        def get_last_mail(self):
            num = self.get_last_mail_index()
            return self.get_mail(num)

        def get_mail(self, index):
            num = index

            last_mail = {
                "index": None,
                "from": None,
                "to": None,
                "subject": None,
                "unix_timestamp": None,
                "body": None,
            }

            if num is not None:
                rv, data = self.mailbox.fetch(num, '(RFC822)')
                if rv == 'OK':
                    msg = email.message_from_string(data[0][1])
                    decode = email.header.decode_header(msg['Subject'])[0]
                    subject = make_unicode(decode[0])

                    last_mail["subject"] = subject
                    last_mail["from"] = msg["from"]
                    last_mail["to"] = msg["to"]
                    last_mail["index"] = num

                    # Now convert to local date-time
                    date_tuple = email.utils.parsedate_tz(msg['Date'])
                    if date_tuple:
                        last_mail["unix_timestamp"] = email.utils.mktime_tz(date_tuple)

                    # get message body
                    body = []
                    if msg.get_content_maintype() == 'multipart': #If message is multi part we only want the text version of the body, this walks the message and gets the body.
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                _ = part.get_payload(decode=True)
                                if len(_) > 0:
                                    body.append(_)
                            elif part.get_content_type() == "text/html":
                                # TODO: This is a workaround for
                                # mail bodies without 'text/plain' section
                                if len(body) == 0:
                                    _ = part.get_payload(decode=True)
                                    if len(_) > 0:
                                        body.append(_)
                            else:
                                continue

                    last_mail["body"] = '\n'.join(body)

            return last_mail


# Base class for Aktos Telemetry Subsystem Mailer
class AktosTelemetryMailBase(EMail):
    def prepare_base(self):
        self.username = "tel@aktos.io"
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
    from aktos_dcs import *
    import time

    # Test if Actors are working while mail is sending
    class TestGevent(Actor):
        def action(self):
            print "Started test action, ", time.time()
            while True:
                print("Hello!, %f" % time.time())
                sleep(0.1)

    TestGevent()

    # Example Usage:
    class TelemetryMail(AktosTelemetryMailBase):
        def prepare(self):
            self.password = "this-is-your-account-password"

    m = TelemetryMail()
    print("sending, %f" % time.time())

    # send a mail
    recipients = ["ceremcem@ceremcem.net"]
    subject = "test-subject-çalışöğün-221234"
    content = "çalışöğün33"
    attachments = ["./cca_signal.py"]
    m.send_mail(recipients, subject, content, attachments)

    # get last mail
    print "Getting mail (blocker)"
    recv = m.get_last_mail()
    for k, v in recv.iteritems():
        print "Entry:", k, "::", v

    print "last mail is %d seconds ago" % (time.time() - recv["unix_timestamp"])

    print("finished: %f" % time.time())
    wait_all()

