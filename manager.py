#!/usr/bin/env python3
from app import create_app, db
from app.models import Role, User, Comment, Follow, Post
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
import os

def make_shell_context():
	return dict(db=db, Role=Role, User=User, Post=Post, Comment=Comment, Follow=Follow)

app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_context=make_shell_context))

@manager.command
def test():
	'''Run the unittest'''
	import unittest
	tests = unittest.TestLoader.discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)

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