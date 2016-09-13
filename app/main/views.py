from . import main
from .forms import EditProfileForm, AdminEditProfileForm, PostForm, CommentForm
from flask import render_template, url_for, redirect, abort, flash, request, \
	current_app, make_response
from flask_login import login_required, current_user
from ..models import User, Role, Post, Comment, Permission, Follow
from .. import db
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
def index():
	form = None
	if current_user.is_authenticated:
		show_all = bool(request.cookies.get('show_all', '1'))
		form = PostForm()
		if form.validate_on_submit():
			post = Post(body=form.post.data, author=current_user._get_current_object())
			db.session.add(post)
			db.session.commit()
			return redirect(url_for('main.index'))
	else:
		show_all = True
	page = request.args.get('page', 1, type=int)
	if show_all:
		pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page=page,
			per_page=current_app.config['POST_PER_PAGE'])
	else:
		pagination = current_user.get_followed_posts().order_by(Post.timestamp.desc()).\
			paginate(page=page,per_page=current_app.config['POST_PER_PAGE'])
	posts = pagination.items
	return render_template('index.html', posts=posts, pagination=pagination, form=form,
		show_all=show_all)

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

@main.route('/user/<username>/status/<id>', methods=['GET', 'POST'])
def user_post(username, id):
	form = None
	post = Post.query.get_or_404(id)
	if current_user.can(Permission.COMMET):
		form = CommentForm()
		if form.validate_on_submit():
			comment = Comment(body=form.comment.data, post=post,
				commentator=current_user._get_current_object())
			db.session.add(comment)
			db.session.commit()
			return redirect(url_for('main.user_post',id=post.id, page=-1,
				username=post.author.username))
	page = request.args.get('page', 1, type=int)
	if page == -1:
		page = (post.comments.count() - 1) // current_app.config['COMMENT_PER_PAGE'] + 1
		print(page)
	pagination = post.comments.order_by(Comment.timestamp.asc()).\
		paginate(page=page, per_page=current_app.config['COMMENT_PER_PAGE'],
			error_out=False)
	return render_template('user-post.html', posts=[post], comments=pagination.items,
		pagination=pagination, username=username, id=id, form=form, page=page)

@main.route('/user/<username>/edit-post/<id>', methods=['GET', 'POST'])
@login_required
def edit_post(username, id):
	post = Post.query.get_or_404(id)
	if current_user.id != post.author.id and not current_user.is_administrator():
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.post.data
		db.session.add(post)
		db.session.commit()
		flash('Your post has been updated.')
		return redirect(url_for('main.user_post', username=username, id=id))
	form.post.data = post.body
	return render_template('edit-post.html', form=form, post=post)

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
	form = AdminEditProfileForm(user=user)
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
@login_required
@permission_required(Permission.ADMINISTER)
def manage_accounts():
	page = request.args.get('page', 1, type=int)
	pagination = User.query.paginate(page=page,
		per_page=current_app.config['POST_PER_PAGE'])
	users = pagination.items
	return render_template('manage-accounts.html', users=users, pagination=pagination)

@main.route('/admin/moderate-comment')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_comment():
	id = request.args.get('id', -1, type=int)
	comment = Comment.query.get_or_404(id)
	comment.disabled ^= True
	db.session.add(comment)
	db.session.commit()
	return redirect(url_for('main.user_post', username=comment.post.author.username,
		id=comment.post.id, page=request.args.get('page', 1, type=int)))

@main.route('/show-all')
def show_all():
	resp = make_response(redirect(url_for('main.index')))
	resp.set_cookie('show_all', '1', max_age=60 * 60 * 24 * 30)
	return resp

@main.route('/show-follow')
@login_required
def show_follow():
	resp = make_response(redirect(url_for('main.index')))
	resp.set_cookie('show_all', '', max_age=60 * 60 * 24 * 30)
	return resp

@main.route('/shutdown')
def server_shutdown():
	if not current_app.testing:
		abort(404)
	shutdown = request.environ.get('werkzeug.server.shutdown')
	if not shutdown:
		abort(500)
	shutdown()
	return 'Shutting down...'