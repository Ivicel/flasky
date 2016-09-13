from . import api
from .authentication import auth
from flask import jsonify, g, request, current_app, url_for
from .decorators import permission_required
from ..models import Permission, Post, Comment, User
from ..exceptions import ValidationError
from app import db


# get all posts
@api.route('/posts/')
@auth.login_required
def get_posts():
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	posts = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_posts', page=page - 1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_posts', page=page + 1, _external=True)
	return jsonify({
		'posts': [post.to_json() for post in posts],
		'prev': prev,
		'next': next,
		'count': pagination.total
	})

# get specified post
@api.route('/posts/<int:id>')
@auth.login_required
def get_post(id):
	post = Post.query.get_or_404(id)
	return jsonify(post.to_json())

# write a new post
@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLE)
def new_post():
	post = Post.from_json(request.get_json())
	post.author = g.current_user
	db.session.add(post)
	db.session.commit()
	return jsonify(post.to_json()), 201, \
		{'Location': url_for('api.get_post', id=post.id, _external=True)}

# update a post
@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLE)
def edit_post(id):
	post = Post.query.get_or_404(id)
	if g.current_user != post.author and not g.current_user.can(Permission.ADMINISTER):
		return forbidden('Insufficient permission.')
	post.body = request.json.get('body', post.body)
	db.session.add(post)
	db.session.commit()
	return jsonify(post.to_json())


# get a user timeline post, include himself
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

# get all posts from user	
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
