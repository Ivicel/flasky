from functools import wraps
from flask import g
from .errors import forbidden


def permission_required(permission):
	def decorate_function(func):
		@wraps(func)
		def decorator(*args, **kwargs):
			if not g.current_user.can(permission):
				return forbidden('you have not permission to make a post')
			return func(*args, **kwargs)
		return decorator
	return decorate_function