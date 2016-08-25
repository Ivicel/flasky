from . import api
from flask import request, jsonify, url_for, current_app
from ..models import Comment


@api.route('/comments/')
def get_comments():
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.paginate(page=page,
		per_page=current_app.config['PER_PAGE'], error_out=False)
	posts = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_comments', page=page - 1, _external=True)
	next = None
	if pagination.has_next:
		next = url_for('api.get_comments', page=page + 1, _external=True)
	return jsonify({
		'comments': [comment.to_json() for comment in comments],
		'prev': prev,
		'next': next,
		'count': pagination.total
	})

@api.route('/comment/<int:id>')
def get_comment(id):
	comment = Comment.query.get_or_404(id)
	return jsonify(comment.to_json())