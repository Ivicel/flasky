from . import main
from .forms import EditProfileForm, AdminEditProfile
from flask import render_template, url_for, redirect, abort, flash, request, \
	current_app
from flask_login import login_required, current_user
from ..models import User, Role, Post, Comment, Permission, Follow
from .. import db
from ..decorators import admin_required, permission_required



@main.route('/')
def index():
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'])
	posts = pagination.items
	return render_template('index.html', posts=posts, pagination=pagination)

@main.route('/user/<username>')
def profile(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.filter_by(author_id=user.id).paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'], error_out=False)
	return render_template('profile.html', user=user, posts=pagination.items,
		pagination=pagination)

@main.route('/user/<username>/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
	if current_user.username != username:
		return redirect(url_for('.edit_profile', username=current_user.username))
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		db.session.add(current_user)
		db.session.commit()
		flash('Your profile has been updated.')
		return redirect(url_for('.edit_profile'), username=username)
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit-profile.html', form=form)

@main.route('/user/<username>/status/<id>')
def user_post(username, id):
	post = Post.query.get_or_404(id)
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.filter_by(post_id=id).order_by(Comment.timestamp.asc()).\
		paginate(page=page, per_page=current_app.config['COMMENT_PER_PAGE'],
			error_out=False)
	return render_template('user-post.html', posts=[post], comments=pagination.items,
		pagination=pagination, username=username, id=id)

@main.route('/user/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def user_follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	current_user.follow(user)
	return redirect(url_for('main.profile', username=username))

@main.route('/user/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def user_unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	current_user.unfollow(user)
	return redirect(url_for('main.profile', username=username))

@main.route('/user/<username>/followers')
def user_followers(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1 ,type=int)
	pagination = user.followers.filter(Follow.follower_id != user.id).paginate(page=page,
		per_page=current_app.config['COMMENT_PER_PAGE'], error_out=False)
	return render_template('followers.html', pagination=pagination, user=user)

@main.route('/user/<username>/followed-by')
def user_followed_by(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1 ,type=int)
	pagination = user.followeds.filter(Follow.followed_id != user.id).paginate(page=page,
		per_page=current_app.config['COMMENT_PER_PAGE'], error_out=False)
	return render_template('followeds.html', pagination=pagination, user=user)

@main.route('/admin/edit-profile/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_profile(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	form = AdminEditProfile(user=user)
	if form.validate_on_submit():
		 user.email = form.email.data
		 user.username = form.username.data
		 user.confirmed = form.confirmed.data
		 user.role_id = form.role.data
		 user.name = form.name.data
		 user.location = form.location.data
		 user.about_me = form.about_me.data
		 db.session.add(user)
		 db.session.commit()
		 flash("user's profile has been updated.")
		 return redirect(url_for('main.admin_edit_profile', username=username))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id or Role.query.filter_by(default_user=True).first().id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit-profile.html', form=form, user=user)

@main.route('/admin/manage-accounts')
def manage_accounts():
	page = request.args.get('page', 1, type=int)
	pagination = User.query.paginate(page=page, per_page=current_app.config['PER_PAGE'])
	users = pagination.items
	return render_template('manage-accounts.html', users=users, pagination=pagination)

