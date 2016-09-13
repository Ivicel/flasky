from . import api
from flask import request, jsonify, url_for, current_app, g
from .. import db
from ..models import Comment, Post

# get a comment info
@api.route('/comment/<int:id>')
def get_comment(id):
	comment = Comment.query.get_or_404(id)
	return jsonify(comment.to_json())

# write a comment on a post
@api.route('/post/<int:id>/write-new-comment', methods=['POST'])
def write_new_comment(id):
	post = Post.query.get_or_404(id)
	body = request.get_json().get('body')
	if not body:
		raise ValidationError('comment does not have a body')
	comment = Comment(body=body, post=post, commentator=g.current_user)
	db.session.add(comment)
	db.session.commit()
	return jsonify(comment.to_json()), 201, \
		{'Location': url_for('api.get_comment', id=comment.id, _external=True)}

# get all comments of a post
@api.route('/post/<int:id>/comments/')
def get_post_comments(id):
	post = Post.query.get_or_404(id)
	page = request.args.get('page', 1, type=int)
	pagination = post.comments.order_by(Comment.timestamp.asc()).\
		paginate(page=page,per_page=current_app.config['POST_PER_PAGE'],
		error_out=False)
	comments = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_post_comments', id=id, page=page - 1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_post_comments', id=id, page=page + 1, _external=True)
	return jsonify({
		'comments': [comment.to_json() for comment in comments],
		'prev': prev,
		'next': next,
		'count': pagination.total
	})

# get all comments form user
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