import os
import subprocess
import time
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


# mail object later in main application
#oMail = cMail()

class pi_mail:
    """ Send Mails back home // Or better call an URL? (or both!) """
    __DIR_PATH_TO_SEND__ = ""

    def __init__(self):
        mail = MIMEMultipart()
        day_time = time.strftime("%Y%m%d_%H%M%S",time.localtime())
        self.mail_from = "la8_doblinger@t-online.de"
        self.mail_to = "pl@loster.com"
        self.mail_subject = "HZ-RR: Bericht vom " + day_time
        self.mail_body = "hz-rr LA8, Bericht vom " + day_time
        self.dir2send = __DIR_PATH_TO_SEND__


    def get(self, var, default_var=""):
        return getattr(self, var, default_var)

    def set(self, var, attr):
        return setattr(self, var, attr)


    def init():
        self.mail['From'] = self.mail_from
        self.mail['To'] = self.mail_to
        self.mail['Subject'] = self.mail_subject


    # smtp-server: securesmtp.t-online.de
    # e-mail:      la8_doblinger@t-online.de
    # pwd:         hzRRemail*                  (für allg. login)
    # email-pwd:   hzRR-la8*                   (speziell für e-mail)

    datime = time.strftime("%Y%m%d_%H%M%S",time.localtime())
    a=os.path.isdir("2send")
    print("directory 2send exists:", a)
    if not a:
        print("'2send' directory does not exist - make it:")
        a=subprocess.call("mkdir 2send", shell=True)
        print(a)

    # try to remove existing files - will be replaced by new ones
    a = subprocess.call("rm -r 2send/Bericht.zip", shell=True)
    print(a)

    a = subprocess.call("/usr/bin/zip -r ./2send/Bericht.zip ./Bilder/", shell=True) # seconds
    print(a)


    mail.attach(MIMEText(body, 'plain'))

    filename = "Bericht.zip"
    attachment = open("./2send/Bericht.zip", "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    msg.attach(part)

    server = smtplib.SMTP('securesmtp.t-online.de', 587)
    server.starttls()
    server.login("la8_doblinger@t-online.de", "hzRR-la8*")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()


    #HZRR_MAIL.py
    fromaddr = "la8_doblinger@t-online.de"
    toaddr = "pl@loster.com"

    msg = MIMEMultipart()

    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "test"
    
    body = "TEst"
    
    msg.attach(MIMEText(body, 'plain'))
    
    filename = "HK1Mod2_20170126_173031.pdf"
    filepath = "Bilder/"+filename
    attachment = open(filepath, "rb")
    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    
    msg.attach(part)
    
    server = smtplib.SMTP('securesmtp.t-online.de', 587)
    server.starttls()
    server.login(fromaddr, "hzRR-la8*")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

    def f(self):
        return 'ffff POG'