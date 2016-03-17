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
            default_imap_port = 993
            default_smtp_port = 587
            self.imap_port = None
            self.smtp_port = None
            self.mail_from = None
            self.username = None
            self.password = None
            self.smtp_server = None
            self.imap_server = None

            self.prepare_base()
            self.prepare()

            # check if class is prepared correctly
            assert self.username is not None
            assert self.password is not None
            assert self.smtp_server is not None
            assert self.imap_server is not None

            # set defaults
            self.imap_port = self.imap_port or default_imap_port
            self.smtp_port = self.smtp_port or default_smtp_port
            self.mail_from = self.mail_from or self.username

            self.smtp_session = None

            # alias functions
            self.send_mail = self.sendMessage

            # login in background
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
            # login to imap session
            self.mailbox = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mailbox.login(self.username, self.password)

            # login to smtp session
            server = smtplib.SMTP(self.smtp_server, port=self.smtp_port)
            server.ehlo()
            # use encrypted SSL mode
            server.starttls()
            # to make starttls work
            server.ehlo()
            server.login(self.username, self.password)
            server.set_debuglevel(self.debug)

            self.smtp_session = server

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
            subject = make_unicode(subject)
            msgContent = make_unicode(msgContent)

            msg = self.prepareMail(mailto, subject, msgContent, files)

            # connect to server and send email
            i = 0
            while True:
                try:
                    failed = self.smtp_session.sendmail(self.mail_from, mailto, msg.as_string())
                    break
                except Exception as er:
                    print er
                    print "INFO: trying to logging in again after %d seconds..." % i
                    gevent.sleep(i)
                    self.login()
                i += 1

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
            last_msg_num = None
            for i in range(20):
                try:
                    resp, received_list = self.mailbox.select("inbox")
                    if resp == "OK":
                        last_msg_num = received_list[0].split()[-1]
                        break
                    else:
                        gevent.sleep(i)
                        assert False
                except:
                    print "INFO: trying to login in order to get mail index..."
                    self.login()
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

