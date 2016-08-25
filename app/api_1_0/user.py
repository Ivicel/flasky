from . import api
from ..models import User, Post, Follow, Comment
from flask import request, jsonify, url_for, abort, current_app


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

@api.route('/user/<username>')
def get_user(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	return jsonify(user.to_json())

@api.route('/user/<username>/timeline/')
def get_user_timeline(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.get_followed_posts.order_by(Post.timestamp.desc()).\
		paginate(page=page, per_page=current_app.config['POST_PER_PAGE'],
		error_out=False)
	posts = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_timeline', username=username,
			page=page - 1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_user_timeline', username=username,
			page=page + 1, _external=True)
	return jsonify({
		'posts': [post.to_json() for post in posts],
		'prev': prev,
		'next': next,
		'count': pagination.total
	})

@api.route('/user/<username>/posts/')
def get_user_posts(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	posts = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_posts', username=username,
			page=page - 1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_user_posts', username=username,
			page=page + 1, _external=True)
	return jsonify({
		'posts': [post.to_json() for post in posts],
		'prev': prev,
		'next': next,
		'count': pagination.total
	})

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

@api.route('/user/<username>/comments/')
def get_user_comments(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.comments.order_by(Comment.timestamp.asc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	comments = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_comments', username=username,
			page=page - 1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_user_comments', username=username,
			page=page + 1, _external=True)
	return jsonify({
		'comments': [comment.to_json() for comment in comments],
		'prev': prev,
		'next': next,
		'count': pagination.total
	})