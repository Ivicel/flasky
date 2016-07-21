from flask_script import Shell, Manager
from flask_migrate import MigrateCommand, Migrate
from config import config
from app import create_app, db
from app.models import Role, User
import unittest
import os

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)
manager = Manager(app)

def make_shell_context():
	return dict(Role=Role, User=User, db=db, app=app)


@manager.command
def test():
	"""Run the unit tests."""
	tests = unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)



if __name__ == '__main__':
	manager.run()