import unittest
from app import create_app, db
from app.models import User, Post, Comment, Role


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

