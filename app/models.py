from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db, login_manager



class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	users = db.relationship('User', backref='role', lazy='dynamic')

	@staticmethod
	def insert_roles():
		roles = ['Administrtor', 'Moderator', 'User']
		for role in roles:
			r = Role.query.filter_by(name=role).first()
			if r is None:
				r = Role(name=role)
				db.session.add(r)
		db.session.commit()

	def __repr__(self):
		return 'In role %s' % self.name

class User(db.Model, UserMixin):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), unique=True, index=True)
	email = db.Column(db.String(64), unique=True, index=True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	password_hash = db.Column(db.String(128))
	confirmed = db.Column(db.Boolean, default=False)
	

	@property
	def password(self):
		raise AttributeError('password is not a readable attribute')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def generate_confirmation_token(self, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'confirm': self.id})

	def confirm(self, token):
		s = Serializer(current_app.config['SECRET_KEY'],)
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed = True
		db.session.add(self)
		db.session.commit()
		return True

	def generate_change_email_token(self, new_email, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({
			'confirm': self.email,
			'new_email': new_email	
		})

	def confirm_new_email(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.email:
			return False
		self.email = data.get('new_email')
		db.session.add(self)
		db.session.commit()
		return True

	def generate_reset_password_token(self, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'confirm': self.email})

	@classmethod
	def confirm_reset_password(cls, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return None
		email = data.get('confirm')
		user = cls.query.filter_by(email=email).first()
		return user

	def __repr__(self):
		return 'In user %s' % self.username


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))