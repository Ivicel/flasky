from . import api
from ..models import User, Post, Follow, Comment
from flask import jsonify, current_app, request, url_for, abort

# 用户信息
@api.route('/user/<username>')
def get_user(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)
	return jsonify(user.to_json())

# 用户posts
@api.route('/user/<username>/posts/')
def get_user_posts(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_posts', username=username, page=page - 1,
			_external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_user_posts', username=username, page=page + 1,
			_external=True)
	return jsonify({
		'posts': [post.to_json() for post in pagination.items],
		'prev': prev,
		'next': next,
		'posts_count': pagination.total
	})

@api.route('/user/<username>/timeline/')
def get_user_timeline(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_timeline', username=username, page=page - 1,
			_external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_user_timeline', username=username, page=page + 1,
			_external=True)
	return jsonify({
		'posts': [post.to_json() for post in pagination.items],
		'prev': prev,
		'next': next,
		'posts_count': pagination.total
	})

# following名单
@api.route('/user/<username>/followed-by/')
def get_user_followed_by(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.followed.filter(Follow.followed_id != user.id).\
		order_by(Follow.timestamp.asc()).paginate(page=page,
		per_page=current_app.config['PER_PAGE'], error_out=False)
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_followed_by', username=username, page=page - 1,
			_external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_user_followed_by', username=username, page=page + 1,
			_external=True)
	return jsonify({
		'users': [f.followed.to_json() for f in pagination.items],
		'prev': prev,
		'next': next,
		'users_count': pagination.total
	})

# follower
@api.route('/user/<username>/followers/')
def get_user_followers(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.followers.filter(Follow.follower_id !=user.id).\
		order_by(Follow.timestamp.asc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_followers', username=username, page=page - 1,
			_external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_user_followers', username=username, page=page + 1,
			_external=True)
	return jsonify({
		'users': [f.follower.to_json() for f in pagination.items],
		'prev': prev,
		'next': next,
		'users_count': pagination.total
	})

@api.route('/user/<username>/comments/', methods=['GET', 'POST'])
def get_user_comments(username):
	user = User.query.filter_by(username=username).first()
	if not user:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.comments.order_by(Comment.timestamp.asc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_user_comments', username=username, page=page - 1,
			_external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_user_comments', username=username, page=page + 1,
			_external=True)
	return jsonify({
		'comments': [comment.to_json() for comment in pagination.items],
		'prev': prev,
		'next': next,
		'comments_count': pagination.total
	})