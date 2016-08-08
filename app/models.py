import hashlib
import bleach
from flask import current_app, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db, login_manager
from datetime import datetime
from forgery_py import forgery
from random import randrange
from markdown import markdown


class Permission:
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE_ARTICLES = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTER = 0x80

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	users = db.relationship('User', backref='role', lazy='dynamic')
	default = db.Column(db.Boolean, default=False, index=True)
	permissions = db.Column(db.Integer)

	@staticmethod
	def insert_roles():
		roles = {
			'User': (Permission.FOLLOW | Permission.COMMENT | 
				Permission.WRITE_ARTICLES, True),
			'Moderator': (Permission.FOLLOW | Permission.COMMENT |
				Permission.WRITE_ARTICLES | Permission.MODERATE_COMMENTS, False),
			'Administrtor': (0xff, False)
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role is None:
				role = Role(name=r)
			role.permissions = roles[r][0]
			role.default = roles[r][1]
			db.session.add(role)
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
	name = db.Column(db.String(64))
	location = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	member_since = db.Column(db.DateTime(), default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
	avatar_hash = db.Column(db.String(128))
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	
	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		if self.role is None:
			if self.email == current_app.config['FLASK_ADMIN']:
				self.role = Role.query.filter_by(permissions=0xff).first()
			if self.role is None:
				self.role = Role.query.filter_by(default=True).first()
		if self.email is not None and self.avatar_hash is None:		
			self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

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
		self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
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

	def can(self, permissions):
		return self.role is not None and \
			(self.role.permissions & permissions) == permissions

	@property
	def is_administrator(self):
		return self.can(Permission.ADMINISTER)

	@is_administrator.setter
	def is_administrator(self, arg):
		raise AttributeError('Attribute can not be set')

	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)
		db.session.commit()

	def generate_avatar(self, size=100, default='identicon', rating='g'):
		if request.is_secure:
			url = 'https://secure.gravatrar.com/avatra'
		else:
			url = 'http://www.gravatar.com/avatar'
		hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
		return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
			url=url, hash=hash, size=size, default=default, rating=rating)

	@staticmethod
	def generate_fake_users():
		for i in range(0, 100):
			username = forgery.internet.user_name()
			email = forgery.internet.email_address()
			if User.query.filter_by(username=username).first() or \
				User.query.filter_by(email=email).first():
				continue
			user = User(username=username, email=email, password='123', confirmed=True)
			user.name = forgery.name.full_name()
			user.location = forgery.name.location()
			user.about_me = forgery.lorem_ipsum.paragraph()
			db.session.add(user)
		db.session.commit()

	def __repr__(self):
		return 'In user %s' % self.username

class AnonymousUser(AnonymousUserMixin):
	def can(self, permissions):
		return False

	@property
	def is_administrator(self):
		return False

	@is_administrator.setter
	def is_administrator(self, arg):
		raise AttributeError('Attribute can not be set')

class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

	@staticmethod
	def generate_fake_posts():
		users = User.query.all()
		for user in users:
			for i in range(0, randrange(1, 2)):
				post = Post(author=user)
				post.body = forgery.lorem_ipsum.paragraphs()
				db.session.add(post)
		db.session.commit()

	@staticmethod
	def on_change_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i',
			'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'p']
		target.body_html = bleach.linkify(bleach.clean(markdown(value,
			output_format='html'), tags=allowed_tags, strip=True))

class Follow(db.Model):
	__tablename__ = 'follows'
	follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
	followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)


db.event.listen(Post.body, 'set', Post.on_change_body)
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))
