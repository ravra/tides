import time, datetime, sys
from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText

SMTPserver    = 'smtp.gmail.com'


def sendMeMail(subject, content):
    sender        = 'foo@blah.net'
    destination   = ['myEmailAddress@gmail.com']
    USERNAME      = "myEmailAddress@gmail.com"
    PASSWORD      = "00000000sameAsNukeCodes"
    text_subtype  = 'plain'

    msg = MIMEText(content, text_subtype)
    msg['Subject']=       subject
    msg['From']   = sender # some SMTP servers will do this automatically, not all

    conn = SMTP(SMTPserver)
    conn.set_debuglevel(False)
    conn.login(USERNAME, PASSWORD)
    try:
        conn.sendmail(sender, destination, msg.as_string())
    finally:
        conn.close()
