from flask import g, request, url_for, jsonify, make_response, redirect
from flask_httpauth import HTTPBasicAuth
from . import api
from .errors import forbidden, unauthorized
from .decorators import permission_required
from ..models import User, Post, AnonymousUser

auth = HTTPBasicAuth()

@api.before_request
@auth.login_required
def before_request():
	if not g.current_user.is_anonymous and not g.current_user.confirmed:
		return unauthorized('Invalid authentication')

@auth.verify_password
def verify_password(email_or_token, password):
	# 匿名用户
	if email_or_token == '':
		g.current_user = AnonymousUser()
		return True
	# 使用 token
	if password == '':
		g.use_token = True
		g.current_user = User.verify_auth_token(email_or_token)
		return g.current_user is not None
	# 使用用户名和密码
	g.current_user = User.query.filter_by(email=email_or_token).first()
	g.use_token = False
	return g.current_user is not None and g.current_user.check_password(password)

@api.route('/token')
def get_token():
	if g.current_user.is_anonymous:
		return forbidden('Invalid user or user is anonymous')
	return jsonify({
		'token': g.current_user.generate_auth_token(expiration=24 * 60 * 60).\
			decode('utf-8')
	})