from flask import Flask, render_template, url_for, session, redirect, request
from flask_bootstrap import Bootstrap
from flask_script import Manager, Command, Shell
from flask_moment import Moment
from datetime import datetime
from flask_wtf import Form
from wtforms import StringField, BooleanField, SubmitField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from wtforms.validators import Email as is_an_email_address
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_mail import Mail, Message
from threading import Thread
import os

base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'This is a very hard to guess key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
	os.path.join(base_dir, 'data.sqlite')
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASK_ADMIN'] = os.environ.get('FLASK_ADMIN')
app.config['FLASK_SUBJECT_PREFIX'] = 'Flasky - '
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
bootstrap = Bootstrap(app)
manager = Manager(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)


def send_mail(to, subject, template, **kwargs):
	msg = Message(app.config['FLASK_SUBJECT_PREFIX'] + subject, recipients=[to])
	msg.html = render_template(template + '.html', **kwargs)
	msg.body = render_template(template + '.txt', **kwargs)
	thr = Thread(target=async_send_mail, name='send_mail', args=(app, msg))
	thr.start()
	return thr

def async_send_mail(app, msg):
	with app.app_context():
		mail.send(msg)
	

class NameForm(Form):
	# email = StringField("Please input your email.", validators=[DataRequired(),
		# is_an_email_address()])
	# password = PasswordField("Input your password.", validators=[DataRequired(),
	# 	EqualTo('password_confirm', "The password looks like not the same.")])
	# password_confirm = PasswordField("Confirm your password.", validators=[
	# 	DataRequired()])
	username = StringField("Please input your name.", validators=[DataRequired()])
	submit = SubmitField("Submit")

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Integer, unique=True)
	users = db.relationship('User', backref='role', lazy='dynamic')

	@staticmethod
	def insert_roles():
		roles = ['Administrator', 'Moderator', 'User']
		for role in roles:
			r = Role.query.filter_by(name=role).first()
			if r is None:
				r = Role(name=role)
				db.session.add(r)
		db.session.commit()

class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True, index=True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

@app.route('/', methods=['GET', 'POST'])
def index():
	form = NameForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None:
			session['known'] = False
			user = User(username=form.username.data)
			db.session.add(user)
			db.session.commit()
			send_mail(app.config['FLASK_ADMIN'], 'New user', 'new_user', user=user)
		else:
			session['known'] = True
		session['username'] = form.username.data
		form.username.data = ''
		return redirect(url_for('index'))
	return render_template('index.html', form=form, known=session.get('known', False),
		username=session.get('username'))


@app.route('/user/<username>')
def user(username):
	return render_template('user.html', username=username)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500


def make_shell_context():
	return dict(app=app, db=db, User=User, Role=Role)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
	manager.run()