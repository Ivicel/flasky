import unittest
import json
import re
from base64 import b64encode
from app import create_app, db
from app.models import Role, User, Follow, Post, Comment
from flask import url_for


class APITestCase(unittest.TestCase):
	def setUp(self):
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()
		Role.insert_roles()
		self.client = self.app.test_client()
		self.app.preprocess_request()

	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()

	def get_auth_headers(self, username, password):
		return {
			'Authorization': 'Basic ' + b64encode(
				(username + ':' + password).encode('utf-8')).decode('utf-8'),
			'Content-Type': 'application/json',
			'Accept': 'application/json'
		}

	def test_no_auth(self):
		response = self.client.get(url_for('api.get_posts'),
			content_type='application/json')
		self.assertTrue(response.status_code == 200)

	def test_404(self):
		response = self.client.get('/not/exist/url/',
			headers=self.get_auth_headers('email', 'passwrod'))
		self.assertTrue(response.status_code == 404)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertTrue(json_response['error'] == 'not found')

	def test_bad_auth(self):
		r = Role.query.filter_by(name='user').first()
		self.assertIsNotNone(r)
		u = User(email='walle@test.com', password='cat', confirmed=True,
			username='walle')
		db.session.add(u)
		db.session.commit()

		# authenticate with none user
		response = self.client.get(url_for('api.get_posts'),
			headers=self.get_auth_headers('not_exsit_user', 'wrong_password'),
			content_type='application/json')
		self.assertEqual(response.status_code, 401)

		# authenticate with wrong password
		response = self.client.get(url_for('api.get_posts'),
			headers=self.get_auth_headers('walle@test.com', 'dog'),
			content_type='application/json')
		self.assertEqual(response.status_code, 401)

	def test_bad_token(self):
		# add a user
		r = Role.query.filter_by(name='user').first()
		self.assertIsNotNone(r)
		u = User(email='walle@test.com', password='cat', confirmed=True,
			username='walle')
		db.session.add(u)
		db.session.commit()

		# authenticate with bad token
		response = self.client.get(url_for('api.get_posts'),
			headers=self.get_auth_headers('bad_token', ''),
			content_type='application/json')
		self.assertEqual(response.status_code, 401)

		# get a token
		response = self.client.get(url_for('api.get_token'),
			headers=self.get_auth_headers('walle@test.com', 'cat'),
			content_type='application/json')
		self.assertEqual(response.status_code, 200)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertIsNotNone(json_response)
		token = json_response.get('token')

		# issue a request with the token
		response = self.client.get(url_for('api.get_posts'),
			headers=self.get_auth_headers(token, ''),
			content_type='application/json')
		self.assertEqual(response.status_code, 200)

	def test_anonymous(self):
		response = self.client.get(url_for('api.get_posts'),
			headers=self.get_auth_headers('', ''),
			content_type='application/json')
		self.assertEqual(response.status_code, 200)

	def test_unconfirmed_account(self):
		# add an unconfirmed account
		r = Role.query.filter_by(name='user').first()
		self.assertIsNotNone(r)
		u = User(email='walle@test.com', password='cat', username='walle')
		db.session.add(u)
		db.session.commit()

		# issue a request with the unconfirmed account
		response = self.client.get(url_for('api.get_posts'),
			headers=self.get_auth_headers('walle@test.com', 'cat'),
			content_type='application/json')
		self.assertEqual(response.status_code, 401)

	def test_posts(self):
		# add a user
		r = Role.query.filter_by(name='user').first()
		self.assertIsNotNone(r)
		u = User(email='walle@test.com', username='walle',
			password='cat', confirmed=True, role=r)
		db.session.add(u)
		db.session.commit()

		# write a post
		response = self.client.post(url_for('api.new_post'), 
			headers=self.get_auth_headers('walle@test.com', 'cat'),
			data=json.dumps({'body': 'body of blog post'}).encode('utf-8'))
		self.assertTrue(response.status_code == 201)
		url = response.headers.get('Location')
		self.assertIsNotNone(url)

		# get the new post
		response = self.client.get(url,
			headers=self.get_auth_headers('walle@test.com', 'cat'))
		self.assertEqual(response.status_code, 200)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertEqual(json_response['url'], url)
		self.assertEqual(json_response['body'], 'body of blog post')
		self.assertEqual(json_response['body_html'], 
			'<p>body of blog post</p>')
		json_post = json_response

		# get posts from user
		response = self.client.get(url_for('api.get_user_posts', username=u.username))
		self.assertEqual(response.status_code, 200)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertIsNotNone(json_response)
		self.assertTrue(json_response.get('count', 0) == 1)
		self.assertTrue(json_response['posts'][0] == json_post)

		# get the post from the user as a follower
		response = self.client.get(url_for('api.get_user_timeline',username=u.username),
			headers=self.get_auth_headers('walle@test.com', 'cat'))
		self.assertEqual(response.status_code, 200)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertIsNotNone(json_response)
		self.assertTrue(json_response.get('count', 0) == 1)
		self.assertEqual(json_response['posts'][0], json_post)

		# edit post
		response = self.client.put(url,
			headers=self.get_auth_headers('walle@test.com', 'cat'),
			data=json.dumps({'body': 'update body'}))
		self.assertEqual(response.status_code, 200)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertEqual(json_response['body'], 'update body')
		self.assertEqual(json_response['url'], url)
		self.assertEqual(json_response['body_html'], '<p>update body</p>')

	def test_users(self):
		# add two users
		r = Role.query.filter_by(name='user').first()
		self.assertIsNotNone(r)
		u1 = User(email='walle@test.com', username='walle', password='cat',
			role=r, confirmed=True)
		u2 = User(email='eve@test.com', username='eve', password='dog',
			role=r, confirmed=True)
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()

		# get users
		response = self.client.get(url_for('api.get_user', username=u1.username,
			headers=self.get_auth_headers('walle@test.com', 'cat')))
		self.assertEqual(response.status_code, 200)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertEqual(json_response['username'], 'walle')
		response = self.client.get(url_for('api.get_user', username=u2.username,
			headers=self.get_auth_headers('walle@test.com', 'cat')))
		self.assertEqual(response.status_code, 200)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertEqual(json_response['username'], 'eve')

	def test_comments(self):
		# add two users
		r = Role.query.filter_by(name='user').first()
		self.assertIsNotNone(r)
		u1 = User(email='walle@test.com', username='walle', password='cat',
			role=r, confirmed=True)
		u2 = User(email='eve@test.com', username='eve', password='dog',
			role=r, confirmed=True)
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()

		# add a post
		post = Post(body='body of the post', author=u1)
		db.session.add(post)
		db.session.commit()

		# write a comment
		response = self.client.post(url_for('api.write_new_comment', id=post.id),
			headers=self.get_auth_headers('eve@test.com', 'dog'),
			data=json.dumps({'body': 'Good [Post](http://www.example.com)'}))
		self.assertTrue(response.status_code == 201)
		json_response = json.loads(response.data.decode('utf-8'))
		url = response.headers.get('Location')
		self.assertIsNotNone(url)
		self.assertTrue(json_response['body'] ==
			'Good [Post](http://www.example.com)')
		self.assertTrue(re.sub(r'<.*?>', '', json_response['body_html']) == 'Good Post')

		# get the new comment
		response = self.client.get(url,
			headers=self.get_auth_headers('walle@test.com', 'cat'))
		self.assertTrue(response.status_code == 200)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertTrue(json_response['url'] == url)
		self.assertTrue(json_response['body'] == 'Good [Post](http://www.example.com)')

		# add another comment
		comment = Comment(body='Thand you!', commentator=u1, post=post)
		db.session.add(comment)
		db.session.commit()

		# get the two comments from the post
		response = self.client.get(url_for('api.get_post_comments', id=post.id,
			headers=self.get_auth_headers('eve@test.com', 'dog')))
		self.assertTrue(response.status_code == 200)
		json_response = json.loads(response.data.decode('utf-8'))
		self.assertIsNotNone(json_response.get('comments'))
		self.assertTrue(json_response.get('count', 0) == 2)
