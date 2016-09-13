import bleach
import hashlib
import random
import re
from markdown import markdown
from datetime import datetime
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from forgery_py import forgery
from app import db, login_manager
from .exceptions import ValidationError


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
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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
	member_since = db.Column(db.DateTime, default=datetime.utcnow)
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)
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
		if self.email is not None and self.avatar_hash is None:
			self.avatar_hash = hashlib.md5(
				self.email.lower().encode('utf-8')).hexdigest()
		if not self.is_following(self):
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
				'new_email': new_email,
				'reset': reset_password
			})
		return s.dumps({
			'confirm': self.id,
			'reset': reset_password
		})

	def confirm_token(self, token, change_email=False):
		s = Serializer(current_app.config['SECRET_KEY'])
		m = False
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') == self.id and not data.get('reset'):
			if change_email and data.get('new_email') is not None:
				self.email = data.get('new_email')
			elif not change_email and data.get('new_email') is None:
				self.confirmed = True
			else:
				return False
			db.session.add(self)
			try:
				db.session.commit()
			except:
				db.session.rollback()
				return False
			return True
		return False
		

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

	def generate_auth_token(self, expiration):
		s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
		return s.dumps({'id': self.id})

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return None
		return User.query.get(data['id'])

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

	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)
		db.session.commit()

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

	@property
	def get_followed_posts(self):
		return Post.query.join(Follow, Post.author_id == Follow.followed_id).\
			filter_by(follower_id=self.id)

	@staticmethod
	def generate_fake_user(num=120):
		for i in range(0, num):
			username = forgery.internet.user_name()
			email = forgery.internet.email_address()
			if User.query.filter_by(username=username).first() is not None or \
				User.query.filter_by(email=email).first() is not None:
				continue
			user = User(username=username, email=email)
			user.password = 'abc123'
			user.confirmed = True
			user.name = forgery.name.full_name()
			user.location = forgery.name.location()
			user.about_me = forgery.lorem_ipsum.sentences()
			db.session.add(user)
			db.session.commit()
		user = User(username='ivicel', email='ivicel@ivicel.com', password='ivicel',
			confirmed=True, role=Role.query.filter_by(permissions=0xff).first())
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

	def to_json(self):
		json_user = {
			'url': url_for('api.get_user', username=self.username, _external=True),
			'username': self.username,
			'member_since': self.member_since,
			'last_seen': self.last_seen,
			'posts': url_for('api.get_user_posts', username=self.username,
				_external=True),
			'following': url_for('api.get_user_following',
				username=self.username, _external=True),
			'post_count': self.posts.count()
		}
		return json_user


class AnonymousUser(AnonymousUserMixin):
	def can(self, permission):
		return False

	def is_administrator(self):
		return False


class Comment(db.Model):
	__tablename__ = 'comments'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)
	commentator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
	disabled = db.Column(db.Boolean, default=False)

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

	@staticmethod
	def on_change_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'i', 'em', 'p', 'b', 'strong', 'abbr', 'acronym', 'code',
			'blockquote']
		target.body_html = bleach.linkify(bleach.clean(markdown(value,
			out_put_format='html5'), tags=allowed_tags, strip=True))

	def to_json(self):
		comment_json = {
			'url': url_for('api.get_comment', id=self.id, _external=True),
			'body': self.body,
			'body_html': self.body_html,
			'commentator': url_for('api.get_user',
				username=self.commentator.username, _external=True),
			'post': url_for('api.get_post', id=self.post.id, _external=True)
		}
		return comment_json

class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)
	comments = db.relationship('Comment', lazy='dynamic', backref='post')
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

	@staticmethod
	def on_change_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'i', 'em', 'b', 'abbr', 'acronym', 'blockquote', 'code',
			'li', 'ol', 'ul', 'pre', 'strong', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']
		target.body_html = bleach.linkify(bleach.clean(markdown(value,
			out_put_format='html5'), tags=allowed_tags, strip=True))

	@staticmethod
	def generate_fake_post(num=120):
		users = User.query.all()
		for i in range(0, num):
			user = random.choice(users)
			post = Post(body=forgery.lorem_ipsum.paragraphs(), author=user)
			db.session.add(post)
		db.session.commit()

	def to_json(self):
		json_post = {
			'url': url_for('api.get_post', id=self.id, _external=True),
			'body': self.body,
			'body_html': self.body_html,
			'timestamp': self.timestamp,
			'author': url_for('api.get_user', username=self.author.username,
				_external=True),
			'comments': url_for('api.get_post_comments', id=self.id, _external=True),
			'comment_count': self.comments.count()
		}
		return json_post

	@staticmethod
	def from_json(json_post):
		body = json_post.get('body')
		if body is None or body == '':
			raise ValidationError('post does not have a body')
		return Post(body=body)

db.event.listen(Post.body, 'set', Post.on_change_body)
db.event.listen(Comment.body, 'set', Comment.on_change_body)
login_manager.anonymous_user = AnonymousUser
from .main import main
@main.app_context_processor
def inject_permissions():
	return dict(Permission=Permission)