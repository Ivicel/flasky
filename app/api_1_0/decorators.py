from functools import wraps
from ..models import Permission
from flask import g
from .errors import forbidden

def permission_required(permission):
	def decorator(func):
		@wraps(func)
		def decorator_function(*args, **kwargs):
			if not g.current_user.can(permission):
				return forbidden("you do not have permission")
			return func(*args, **kwargs)
		return decorator_function
	return decorator