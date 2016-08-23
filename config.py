import os

base_dir = os.path.abspath(os.path.dirname(__name__))

class Config:
	SQLALCHEMY_TRACK_MODIFICATIONS = True
	FLASK_MAIL_PREFIX = '[Flasky]'
	FLASK_ADMIN = os.environ.get('FLASK_ADMIN')
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_DEFAULT_SENDER = '<Flasky> admin@example.com'
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	POST_PER_PAGE = 10
	COMMENT_PER_PAGE = 7
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess key'


	@staticmethod
	def init_app(app):
		pass


class DevelopmentConfig(Config):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE') or \
		'sqlite:///' + os.path.join(base_dir, 'data-dev.sqlite')

class TestingConfig(Config):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE') or \
		'sqlite:///' + os.path.join(base_dir, 'data-test.sqlite')

class ProductionConfig(Config):
	SQLALCHEMY_DATABASE_URI = os.environ.get('PRODUCT_DATABASE') or \
		'sqlite:///' + os.path.join(base_dir, 'data-sqlite')

config = {
	'testing': TestingConfig,
	'development': DevelopmentConfig,
	'production': ProductionConfig,
	'default': DevelopmentConfig
}