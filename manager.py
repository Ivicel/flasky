#!/usr/bin/env python3
import os
COV = None
if os.environ.get('FLASK_COVERAGE'):
	import coverage
	COV = coverage.Coverage(branch=True, include='app/*')
	COV.start()

from app import create_app, db
from app.models import Role, User, Comment, Follow, Post
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

def make_shell_context():
	return dict(db=db, Role=Role, User=User, Post=Post, Comment=Comment, Follow=Follow)

app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_context=make_shell_context))


@manager.command
def test(coverage=False):
	'''Run the unittest'''
	if coverage and not os.environ.get('FLASK_COVERAGE'):
		import sys
		os.environ['FLASK_COVERAGE'] = '1'
		os.execvp(sys.executable, [sys.executable] + sys.argv)
	import unittest
	tests = unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)
	if COV:
		COV.stop()
		COV.save()
		print('Coverage Summary:')
		COV.report()
		basedir = os.path.abspath(os.path.dirname(__file__))
		covdir = os.path.join(basedir, 'tmp/coverage')
		COV.html_report(directory=covdir)
		print('HTML version: file://%s/index.html' % covdir)
		COV.erase()

@manager.command
def renew():
	db.drop_all()
	db.create_all()
	Role.insert_roles()
	User.generate_fake_user()
	Post.generate_fake_post()
	Comment.generate_fake_comment()
	Follow.generate_fake_follow()

if __name__ == '__main__':
	manager.run()