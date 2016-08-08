from flask import render_template, url_for, redirect, session, current_app, abort, \
	flash, request
from flask_login import login_required, current_user
from .. import db
from . import main
from ..models import Role, User, Permission, Post
from .forms import PostForm, EditProfileForm, EditProfileAdminForm
from ..email import send_mail
from ..decorators import admin_required, permission_required

@main.route('/', methods=['GET', 'POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and \
		form.validate_on_submit():
		post = Post(body=form.body.data, author=current_user._get_current_object())
		db.session.add(post)
		db.session.commit()
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
		page=page, per_page=current_app.config['PER_PAGE'])
	return render_template('index.html', form=form, posts=pagination.items, 
		pagination=pagination)

@main.route('/user/<username>')
def user_profile(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.filter_by(author_id=user.id).order_by(
		Post.timestamp.desc()).paginate(page=page,
		per_page=current_app.config['PER_PAGE'])
	return render_template('user-profile.html', user=user, posts=pagination.items,
		pagination=pagination)

@main.route('/user/<username>/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
	if User.query.filter_by(username=username).first() != current_user:
		abort(404)
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		db.session.add(current_user)
		db.session.commit()
		flash('Your profile has been updated.')
		return redirect(url_for('.user_profile', username=current_user.username))
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	title = 'Edit your profile'
	return render_template('auth/register.html', form=form, title=title)

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user=user)
	if form.validate_on_submit():
		user.email = form.email.data
		user.username = form.username.data
		user.confirmed = form.confirmed.data
		user.role = Role.query.get(form.role.data)
		user.name = form.name.data
		user.location = form.location.data
		user.about_me = form.about_me.data
		db.session.add(user)
		db.session.commit()
		flash('The profile has been updated.')
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	title = 'Edit user profile[Admin]'
	return render_template('auth/register.html', form=form, title=title)

@main.route('/manage-accounts')
@admin_required
def manage_account():
	page = request.args.get('page', 1, type=int)
	pagination = User.query.order_by(User.username.asc()).paginate(page=page,
		per_page=current_app.config['PER_PAGE'])
	return render_template('manage-accounts.html', users=pagination.items,
		pagination=pagination)

@main.route('/post/<int:id>')
def post_link(id):
	post = Post.query.filter_by(id=id).first()
	if post is None:
		abort(404)
	return render_template('post-link-page.html', posts=[post])

@main.route('/edit-post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
	form = PostForm()
	post = Post.query.get_or_404(id)
	if post.author != current_user or not current_user.is_administrator:
		abort(403)
	if form.validate_on_submit():
		post.body = form.body.data
		db.session.add(post)
		db.session.commit()
		return redirect(url_for('main.edit_post', id=post.id))
	form.body.data = post.body
	return render_template('edit-post.html', form=form)