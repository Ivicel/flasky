from . import api
from ..models import User, Post, Follow, Comment
from flask import request, jsonify, url_for, abort, current_app

# get all users
@api.route('/users/')
def get_users():
	page = request.args.get('page', 1, type=int)
	pagination = User.query.paginate(page=page,
		per_page=current_app.config['PER_PAGE'], error_out=False)
	posts = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_users', page=page - 1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_users', page=page + 1, _external=True)
	return jsonify({
		'users': [user.to_json() for user in users],
		'prev': prev,
		'next': next,
		'count': pagination.total
	})

# get a specified
@api.route('/user/<username>')
def get_user(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	return jsonify(user.to_json())

# get all users followed by sepcified user
@api.route('/user/<username>/following/')
def get_user_following(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.followeds.filter(Follow.followed_id != user.id).\
		order_by(Follow.timestamp.asc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	users = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_following', username=username,
			page=page - 1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_user_following', username=username,
			page=page + 1, _external=True)
	return jsonify({
		'users': [f.followed.to_json() for f in users],
		'prev': prev,
		'next': next,
		'count': pagination.total
	})

