from flask import request, g, current_app, jsonify, url_for
from . import api
from ..models import Post, Permission
from .decorators import permission_required
from .errors import forbidden
from app import db

@api.route('/posts/')
def get_posts():
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	prev = None
	next = None
	if pagination.has_prev:
		prev = url_for('api.get_posts', page=prev, _external=True)		
	if pagination.has_next:
		next = url_for('api.get_posts', page=next, _external=True)
	posts = {
		'posts': [post.to_json() for post in pagination.items],
		'prev': prev,
		'next': next,
		'posts_count': pagination.total
	}
	return jsonify(posts)

@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def compose_post():
	body = request.get_json().get('body')
	if not body:
		return forbidden('post can not be null')
	post = Post(body=body, author=g.current_user)
	db.session.add(post)
	db.session.commit()
	return jsonify({
		'message': 'post success',
		'post': post.to_json()
	})

@api.route('/post/<int:id>')
def get_post(id):
	post = Post.query.get_or_404(id)
	return jsonify(post.to_json())

@api.route('/post/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
	post = Post.query.get_or_404(id)
	if g.current_user != post.author and not g.current_user.is_adminstrator():
		return forbidden('Insufficient permissions')
	if not request.get_json().get('body'):
		return forbidden('post can not be null')
	post.body = request.get_json().get('body')
	db.session.add(post)
	return jsonify(post.to_json())

@api.route('/post/<int:id>/comments/')
def get_post_comments(id):
	post = Post.query.get_or_404(id)
	page = request.args.get('page', 1, type=int)
	pagination = post.comments.paginate(page=page,
		per_page=current_app.config['FLASK_COMMENTS_PER_PAGE'], error_out=False)
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_post_comments', id=post.id, page=page - 1,
			_external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_post_comments', id=post.id, page=page + 1,
			_external=True)
	return jsonify({
		'comments': [comment.to_json() for comment in pagination.items],
		'prev': prev,
		'next': next,
		'comments_count': post.comments.count()
	})