from . import main
from flask import render_template, url_for, redirect





@main.route('/')
def index():
	return render_template('index.html')

@main.route('/user/<username>')
def profile(username):
	pass