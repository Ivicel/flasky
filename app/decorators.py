from flask_login import current_user
from functools import wraps

def permission_required(permission):
	def decorator(f):
		@wraps(f)
		def decorator_function(*args, **kwargs):
			if not current_user.can(permission):
				abort(403)
			return f(*args, **kwargs)
		return decorator_function
	return decorator

def admin_required(f):
	return permission_required(Permission.ADMINISTER)(f)