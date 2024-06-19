import os
from flask_mail import Message

def user_mail(title, body, email):
    from project import mail
    msg = Message(title, sender=os.environ['MAIL_USERNAME'], recipients=[email])
    msg.body = body
    mail.send(msg)
