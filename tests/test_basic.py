import unittest
from app import create_app, db


class TestBasic(unittest.TestCase):
	def setUp(self):
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()

	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()

	def test_app_exist(self):
		self.assertIsNotNone(self.app)

	def test_is_testing(self):
		self.assertTrue(self.app.config['TESTING'])