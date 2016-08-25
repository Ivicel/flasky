from flask import request, jsonify, g
from flask_httpauth import HTTPBasicAuth
from . import api
from .errors import unauthorized, forbidden
from ..models import AnonymousUser, User

auth = HTTPBasicAuth()


@api.before_request
@auth.login_required
def before_request():
	if not g.current_user.is_anonymous and not g.current_user.confirmed:
		return forbidden('Unconfirm account')

@auth.verify_password
def verify_password(email_or_token, password):
	if email_or_token == '':
		g.current_user = AnonymousUser()
		return True
	if password == '':
		g.token_used = True
		g.current_user = User.verify_auth_token(email_or_token)
		return g.current_user is not None
	user = User.query.filter_by(email=email_or_token).first()
	if user is None:
		return False
	g.current_user = user
	g.token_used = False
	return user.verify_password(password)

@auth.error_handler
def error_handle():
	return unauthorized('Invalid credentials')


@api.route('/token')
def get_token():
	if g.current_user.is_anonymous or g.token_used:
		return unauthorized('Invalid credentials')
	return jsonify({
		'token': g.current_user.generate_auth_token(expiration=24 * 60 * 60).decode('utf-8')
	})

