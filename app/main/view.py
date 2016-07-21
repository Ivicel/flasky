from flask import render_template, url_for, redirect, session, current_app
from flask_login import login_required
from .. import db
from . import main
from ..models import Role, User
from .forms import NameForm
from ..email import send_mail

@main.route('/', methods=['GET', 'POST'])
def index():
	form = NameForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None:
			session['known'] = False
			user = User(username=form.username.data)
			db.session.add(user)
			db.session.commit()
			send_mail(current_app.config['FLASK_ADMIN'], 'New user', 'new_user',
				user=user)
		else:
			session['known'] = True
		session['username'] = form.username.data
		form.username.data = ''
		return redirect(url_for('.index'))
	return render_template('index.html', form=form, known=session.get('known', False),
		username=session.get('username'))

@main.route('/user/<username>')
@login_required
def user_profile(username):
	return render_template('user-profile.html', username=username)