from smtplib import SMTP
from sqlog_logic import SQLog
import ConfigParser

class Email(object):

    def __init__(self):
        
        self.logic = SQLog()
        self.config = ConfigParser.RawConfigParser()
        try:
            self.config.read('config.ini')
        except Exception as e:
            print "Could read config.ini. Reason: %s" % e 
            sys.exit(1)

    def send_email(self, message):
        """ If you are using GMAIL see, https://support.google.com/mail/answer/78754 """
        try:
            from smtplib import SMTP
            smtp = SMTP()
            smtp.connect(self.config.get("notifications", "smtp_server"), 
                         self.config.get("notifications", "smtp_port"))
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(self.config.get("notifications", "email_address"), 
                       self.config.get("notifications", "password"))
            smtp.sendmail(self.config.get("notifications", "email_address"), 
                          self.config.get("notifications", "email_address"),
                          str(message))
        except Exception as e:
            log = "Could not send E-mail notification. Reason: %s" % e
            self.logic.logger(log)
            return False
        return True
