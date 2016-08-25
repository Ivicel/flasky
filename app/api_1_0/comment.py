from . import api
from ..models import Comment
from flask import request, current_app, jsonify, url_for


@api.route('/comments/')
def get_comments():
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.order_by(Comment.timestamp.asc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_comments', page=page - 1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_comments', page=page + 1, _external=True)
	return jsonify({
		'comments': [comment.to_json() for comment in pagination.items],
		'prev': prev,
		'next': next,
		'comments_count': pagination.total
	})

@api.route('/comment/<int:id>')
def get_comment(id):
	comment = Comment.query.get_or_404(id)
	return jsonify(comment.to_json())