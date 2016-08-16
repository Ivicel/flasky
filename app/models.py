import hashlib
import random
from . import db
from datetime import datetime
from flask import current_app
from forgery_py import forgery
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

class Permission:
	"""FOLLOW: 关注其他人
	COMMENT: 评论其他人post
	WRITE_ARTICLE: 发表post
	MODERATE_COMMENTS: 修改他人评论
	ADMINISTER: 管理网站
	"""
	FOLLOW = 0x01
	COMMET = 0X02
	WRITE_ARTICLE = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTER = 0x80

class Follow(db.Model):
	__tablename__ = 'follows'
	id = db.Column(db.Integer, primary_key=True)
	follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
	followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
	timestamp = db.Column(db.Date, default=datetime.utcnow)

	@staticmethod
	def generate_fake_follow():
		users = User.query.all()
		for i in range(0, 100):
			u1 = random.choice(users)
			u2 = random.choice(users)
			if not u1.is_following(u2):
				u1.follow(u2)

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64))
	user = db.relationship('User', backref='role', lazy='dynamic')
	permissions = db.Column(db.Integer)
	default_user = db.Column(db.Boolean, default=False, index=True)

	@staticmethod
	def insert_roles():
		roles = {
			'user': (Permission.FOLLOW | Permission.COMMET | \
				Permission.WRITE_ARTICLE, True),
			'Moderator': (Permission.FOLLOW | Permission.COMMET | \
				Permission.WRITE_ARTICLE | Permission.MODERATE_COMMENTS, False),
			'Administrator': (0xff, False)
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role is None:
				role = Role(name=r)
			role.permissions = roles[r][0]
			role.default_user = roles[r][1]
			db.session.add(role)
		db.session.commit()

class User(db.Model, UserMixin):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(128), unique=True, index=True)
	email = db.Column(db.String(128), unique=True, index=True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	password_hash = db.Column(db.String(128))
	confirmed = db.Column(db.Boolean, default=False)
	name = db.Column(db.String(64))
	location = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	avatar_hash = db.Column(db.String(128))
	member_since = db.Column(db.Date, default=datetime.utcnow)
	last_seen = db.Column(db.Date, default=datetime.utcnow)
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	comments = db.relationship('Comment', backref='commentator', lazy='dynamic')
	followers = db.relationship('Follow', backref=db.backref('followed', lazy='joined'),
		foreign_keys=[Follow.followed_id], lazy='dynamic', cascade='all, delete-orphan')
	followeds = db.relationship('Follow', backref=db.backref('follower', lazy='joined'),
		foreign_keys=[Follow.follower_id], lazy='dynamic', cascade='all, delete-orphan')

	def __init__(self, *args, **kwargs):
		super(User, self).__init__(*args, **kwargs)
		if self.role is None:
			if self.email == current_app.config['FLASK_ADMIN']:
				self.role = Role.query.filter_by(permissions=0xff).first()
		if self.role is None:
			self.role = Role.query.filter_by(default_user=True).first()
		self.avatar_hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
		self.follow(self)

	@property
	def password(self):
		raise AttributeError('password is not a reachable attribute.')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def generate_token(self, expiration=3600, new_email=None, reset_password=False):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		if new_email is not None and not reset_password:
			return s.dumps({
				'confirm': self.id,
				'new_email': new_email
			})
		return s.dumps({
			'confirm': self.id,
			'reset': reset_password
		})

	def confirm_token(self, token, change_email=False):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') == self.id:
			if data.get('reset') is not None and not change_email:
				self.confirmed = True
			elif data.get('new_email') is not None and change_email:
				self.email = data.get('new_email')
			else:
				return False
		else:
			return False
		db.session.add(self)
		db.session.commit()
		return True

	@staticmethod
	def confirm_reset_password(token, password):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if not data.get('reset'):
			return False
		user = User.query.filter_by(id=data.get('confirm')).first()
		if user is None:
			return False
		user.password = password
		db.session.add(user)
		db.session.commit()
		return True

	def can(self, permission):
		try:
			return self.role is not None and \
				(self.role.permissions & permission) == permission
		except:
			return False

	def is_administrator(self):
		return self.can(Permission.ADMINISTER)

	def generate_avatar(self, size=300, default="identicon", rate='g'):
		email_hash = self.avatar_hash or \
			hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
		url = 'https://www.gravatar.com/avatar/' + email_hash
		return '{url}?default={default}&r={rate}&size={size}'.format(url=url, 
			default=default, rate=rate, size=size)

	def is_following(self, user):
		return self.followeds.filter_by(followed_id=user.id).first() is not None

	def is_followed_by(self, user):
		return self.followers.filter_by(follower_id=user.id).first() is not None

	def follow(self, user):
		if not self.is_following(user):
			f = Follow(follower=self, followed=user)
			db.session.add(f)
			db.session.commit()

	def unfollow(self, user):
		if self.is_following(user):
			f = self.followeds.filter_by(followed_id=user.id).first()
			db.session.delete(f)
			db.session.commit()

	@staticmethod
	def generate_fake_user():
		for i in range(0, 120):
			username = forgery.internet.user_name()
			email = forgery.internet.email_address()
			if User.query.filter_by(username=username).first() is not None or \
				User.query.filter_by(email=email).first() is not None:
				continue
			user = User(username=username, email=email)
			print('aaaaaaaaaaa---------------------------       ' + user.email)
			user.password = 'abc123'
			user.confirmed = True
			user.name = forgery.name.full_name()
			user.location = forgery.name.location()
			user.about_me = forgery.lorem_ipsum.sentences()
			db.session.add(user)
			db.session.commit()

	@staticmethod
	def update_user_info():
		users = User.query.all()
		default_user = Role.query.filter_by(default_user=True).first()
		for user in users:
			if True or user.avatar_hash is None:
				user.avatar_hash = hashlib.md5(
					user.email.lower().encode('utf-8')).hexdigest()
			if user.role is None:
				user.role = default_user
			db.session.add(user)
		db.session.commit()

class AnonymousUser(AnonymousUserMixin):
	def can(self, permission):
		return False

	def is_administrator(self):
		return False

class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.Date, default=datetime.utcnow)
	comments = db.relationship('Comment', lazy='dynamic', backref='post')
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

	def body_on_change(self):
		self.body_html = self.body
		db.session.add(self)
		db.session.commit()

	@staticmethod
	def generate_fake_post():
		users = User.query.all()
		for i in range(0, 120):
			user = random.choice(users)
			post = Post(body=forgery.lorem_ipsum.paragraphs(), author=user)
			db.session.add(post)
		db.session.commit()

class Comment(db.Model):
	__tablename__ = 'comments'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.Date, default=datetime.utcnow)
	commentator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

	@staticmethod
	def generate_fake_comment():
		posts = Post.query.all()
		users = User.query.all()
		for post in posts:
			for i in range(0, 10):
				user = random.choice(users)
				comment = Comment(body=forgery.lorem_ipsum.paragraphs(),
					commentator=user, post=post)
				db.session.add(user)
			db.session.commit()
