from flask import Blueprint
from ..models import Permission

main = Blueprint('main', __name__)

from . import view, errors

# 让所有模版都可以访问Permission类
@main.app_context_processor
def inject_permission():
	return dict(Permission=Permission)