from . import api



@api.route('/post/<int:id>/comments/')
def get_post_comments(id):
	pass
