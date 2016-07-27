from . import mail
from flask_mail import Message
from flask import render_template, current_app
from threading import Thread


def send_mail(to, subject, template, **kwargs):
	msg = Message(subject=subject, recipients=[to])
	msg.body = render_template(template + '.txt', **kwargs)
	msg.html = render_template(template + '.html', **kwargs)
	thr = Thread(target=async_send_mail, args=[current_app._get_current_object(), msg])
	thr.start()

def async_send_mail(app, msg):
	with app.app_context():
		mail.send(msg)