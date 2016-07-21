from flask import current_app, render_template
from threading import Thread
from flask_mail import Message
from . import mail

def send_mail(to, subject, template, **kwargs):
	msg = Message(current_app.config['FLASK_SUBJECT_PREFIX'] + subject, recipients=[to])
	msg.html = render_template(template + '.html', **kwargs)
	msg.body = render_template(template + '.txt', **kwargs)
	thr = Thread(target=async_send_mail, name='send_mail', args=(current_app._get_current_object(), msg))
	thr.start()
	return thr

def async_send_mail(app, msg):
	with app.app_context():
		mail.send(msg)


