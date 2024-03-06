from app import app, db
from flask import render_template, redirect, url_for, flash, request, abort
from app.models import User, Post
from app.forms import RegisterForm, LoginForm, CreatePostForm, EditPostForm, DeletePostForm
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError


@app.route('/')
def root():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    else:
        return redirect(url_for('login_page'))
    
    
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        flash("Already authenticated!")
        return redirect(url_for('home_page'))
    
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(form.password.data):
            login_user(attempted_user)
            flash(f'Success! You are now logged in as: {attempted_user.username}', category='success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home_page'))
        else:
            flash('Username and password do not match! Please try again', category='danger')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        flash("Already authenticated!")
        return redirect(url_for('home_page'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email_address.data
        password = form.password1.data

        # Check if the username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists! Please try a different username.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email_address=email).first():
            flash('Email Address already exists! Please try a different email address.', 'danger')
            return redirect(url_for('register'))

        # Create a new user if username and email are unique
        try:
            user = User(username=username, email_address=email, password=password)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login_page'))
        except IntegrityError:
            db.session.rollback()
            flash('An unexpected error occurred. Please try again later.', 'danger')
            return redirect(url_for('register_page'))

    return render_template('register.html', form=form)


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home_page():
    create_post_form = CreatePostForm()
    edit_post_form = EditPostForm()
    delete_post_form = DeletePostForm()

    if request.method == "POST":
        pass

    if request.method == "GET":
        posts = Post.query.all()
        return render_template('home.html', posts=posts, create_post_form=create_post_form, 
                               edit_post_form=edit_post_form, delete_post_form=delete_post_form)


    return render_template('home.html')


@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = Post(title=form.title.data, description=form.description.data, owned_user=current_user)
        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully!', category='success')
    else:
        flash('Error creating post. Please try again.', category='danger')
    return redirect(url_for('home_page'))


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owned_user != current_user:
        abort(403)
    form = EditPostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.description = form.description.data
        db.session.commit()
        flash('Post updated successfully!', category='success')
        return redirect(url_for('home_page'))
    elif request.method == 'GET':
        form.title.data = post.title
        form.description.data = post.description
    return render_template('edit_post.html', form=form)


@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owned_user != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', category='success')
    return redirect(url_for('home_page'))


@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("login_page"))