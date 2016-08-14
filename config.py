import os

base_dir = os.path.abspath(os.path.dirname(__file__))


class Config:
	FLASK_ADMIN = os.environ.get('FLASK_ADMIN')
	FLASK_MAIL_SUBJECT_PREFIX = '[Flasky]'
	SECRET_KEY = 'This is a very hard to guess key'
	MAIL_DEFAULT_SENDER = '<Flask> ' + os.environ.get('FLASK_ADMIN')
	FLASK_SUBJECT_PREFIX = '[Flasky]'
	SQLALCHEMY_TRACK_MODIFICATIONS = True
	PER_PAGE = 10
	FLASK_COMMENTS_PER_PAGE = 5


	@staticmethod
	def init_app(app):
		pass

class DevelopmentConfig(Config):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_dir, 'data-dev.sqlite')
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	MAIL_PORT = 587
	MAIL_USE_TLS = True

class TestConfig(Config):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_dir, 'data-test.sqlite')

class ProductionConfig(Config):
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_dir, 'data.sqlite')

config = {
	'developemnt': DevelopmentConfig,
	'testing': TestConfig,
	'production': ProductionConfig,
	'default': DevelopmentConfig
}
