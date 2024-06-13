
from flask_mail import Message

def user_mail(title, body, email):
    from project import mail
    msg = Message(title, sender="faizandiwan921@gmail.com", recipients=[email])
    msg.body = body
    mail.send(msg)
