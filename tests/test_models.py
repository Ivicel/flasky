import unittest
import sqlalchemy
import time
from datetime import datetime
from app import create_app, db
from app.models import User, Post, Comment, Role, Permission, AnonymousUser, Follow



class TestModels(unittest.TestCase):
	def setUp(self):
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()
		Role.insert_roles()

	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()

	def test_user_password(self):
		u = User(password='cat')
		self.assertIsNotNone(u.password_hash)

	def test_no_password_getter(self):
		u = User(password='cat')
		with self.assertRaises(AttributeError):
			u.password

	def test_verify_password(self):
		u = User(password='cat')
		self.assertTrue(u.check_password('cat'))
		self.assertFalse(u.check_password('dog'))

	def test_password_salts_are_random(self):
		u1 = User(password='cat')
		u2 = User(password='cat')
		self.assertTrue(u1.password_hash != u2.password_hash)

	def test_register_change_email_reset_password_token(self):
		u1 = User(email='walle@test.com', password='cat')
		u2 = User(email='eve@test.com')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		t1_confirm = u1.generate_token()
		t1_change_email = u1.generate_token(new_email='walle@example.com')
		t1_reset_password = u1.generate_token(reset_password=True)

		self.assertTrue(u1.confirm_token(t1_confirm))
		self.assertFalse(u1.confirm_token(t1_change_email))
		self.assertFalse(u1.confirm_token(t1_reset_password))

		self.assertTrue(u1.confirm_token(t1_change_email, change_email=True))
		self.assertFalse(u1.confirm_token(t1_confirm, change_email=True))
		self.assertFalse(u1.confirm_token(t1_reset_password, change_email=True))

		self.assertTrue(User.confirm_reset_password(t1_reset_password, 'dog'))
		self.assertFalse(User.confirm_reset_password(t1_confirm, 'dog'))
		self.assertFalse(User.confirm_reset_password(t1_change_email, 'dog'))

		self.assertFalse(u2.confirm_token(t1_confirm))
		self.assertFalse(u2.confirm_token(t1_change_email, 'eve@example.com'))

	def test_duplicate_email_change_token(self):
		u1 = User(email='walle@test.com', password='cat')
		u2 = User(email='eve@test.com', password='cat')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		token = u2.generate_token(new_email='walle@test.com')
		self.assertFalse(u2.confirm_token(token, change_email=True))
		self.assertTrue(u2.email == 'eve@test.com')

	def test_roles_and_permission(self):
		u = User(email='walle@test.com', password='cat')
		self.assertTrue(u.can(Permission.WRITE_ARTICLE))
		self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

	def test_anonymous_user(self):
		u = AnonymousUser()
		self.assertFalse(u.can(Permission.WRITE_ARTICLE))

	def test_timestamps(self):
		u = User(password='cat')
		db.session.add(u)
		db.session.commit()
		self.assertTrue((datetime.utcnow() - u.member_since).total_seconds() < 3)
		self.assertTrue((datetime.utcnow() - u.last_seen).total_seconds() < 3)

	def test_ping(self):
		u = User(password='cat')
		db.session.add(u)
		db.session.commit()
		time.sleep(2)
		last_seen_before = u.last_seen
		u.ping()
		self.assertTrue(u.last_seen > last_seen_before)

	def test_gravatar(self):
		u = User(email='walle@test.com', password='cat')
		with self.app.test_request_context('/'):
			gravatar = u.generate_avatar()
			gravatar_256 = u.generate_avatar(size=256)
			gravatar_pg = u.generate_avatar(rate='pg')
			gravatar_retro = u.generate_avatar(default='retro')
		with self.app.test_request_context('/', base_url='https://example.com'):
			gravatar_ssl = u.generate_avatar()
		self.assertTrue('https://www.gravatar.com/avatar/'
			'3519e93c7422094126d16e0e4c1e80f9' in gravatar)
		self.assertTrue('size=256' in gravatar_256)
		self.assertTrue('r=pg' in gravatar_pg)
		self.assertTrue('default=retro' in gravatar_retro)
		self.assertTrue('https' in gravatar_ssl)

	def test_follows(self):
		u1 = User(email='walle@test.com', password='cat')
		u2 = User(email='eve@test.com', password='dog')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		self.assertFalse(u1.is_following(u2))
		self.assertFalse(u1.is_followed_by(u2))
		timestamp_before = datetime.utcnow()
		u1.follow(u2)
		db.session.add(u1)
		db.session.commit()
		timestamp_after = datetime.utcnow()
		self.assertTrue(u1.is_following(u2))
		self.assertFalse(u1.is_followed_by(u2))
		self.assertTrue(u2.is_followed_by(u1))
		self.assertFalse(u2.is_following(u1))
		self.assertTrue(u1.followeds.count() == 2)
		self.assertTrue(u2.followers.count() == 2)
		f = u1.followeds.all()[-1]
		self.assertTrue(f.followed == u2)
		self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
		f = u2.followers.all()[-1]
		self.assertTrue(f.follower == u1)
		u1.unfollow(u2)
		db.session.add(u1)
		db.session.commit()
		self.assertTrue(u1.followeds.count() == 1)
		self.assertTrue(u2.followers.count() == 1)
		self.assertTrue(Follow.query.count() == 2)
		u2.follow(u1)
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		db.session.delete(u2)
		db.session.commit()
		self.assertTrue(Follow.query.count() == 1)

	def test_to_json(self):
		u = User(email='walle@test.com', username='walle', password='cat')
		db.session.add(u)
		db.session.commit()
		json_user = u.to_json()
		expected_keys = ['url', 'username', 'member_since', 'last_seen', 'posts',
			'following', 'post_count']
		self.assertEqual(sorted(expected_keys), sorted(json_user.keys()))
		self.assertTrue('api/v1.0/user' in json_user['url'])