from app import app, db, login_manager
from flask import render_template, redirect, url_for, flash, request, abort
from app.models import User, Post
from app.forms import RegisterForm, LoginForm, CreatePostForm, EditPostForm, DeletePostForm, ForgotPasswordForm
from flask_login import login_user, logout_user, login_required, current_user

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def root():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    else:
        return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        flash("You are already authenticated!")
        return redirect(url_for('home_page'))
    
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password(form.password.data):
            login_user(attempted_user)
            flash(f'Success! You are now logged in as: {attempted_user.username}', category='success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home_page'))
        flash('There was an error logging in. Please try again.', category='danger')
    return render_template('login.html', form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        new_password = form.password1.data

        user = User.query.filter_by(username=username, email_address=email).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            flash('Password has been reset successfully.', 'success')
            return redirect(url_for('login_page'))
        else:
            flash('User with provided credentials does not exist.', 'danger')
    return render_template('forgot_password.html', form=form)

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
        
        try:
            user = User(username=username, email_address=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login_page'))
        except Exception as e:
            flash('An unexpected error occurred. Please try again later.', 'danger')
            app.logger.error(f"Error while registering user: {str(e)}")
            return render_template('register.html', form=form)

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return render_template('register.html', form=form)

@app.route('/home', methods=['GET'])
@login_required
def home_page():
    create_post_form = CreatePostForm()
    edit_post_form = EditPostForm()
    delete_post_form = DeletePostForm()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # Default to 10 entries per page

    posts = Post.query.paginate(page=page, per_page=per_page)
    
    return render_template('home.html', posts=posts, create_post_form=create_post_form, 
                           edit_post_form=edit_post_form, delete_post_form=delete_post_form)

@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = Post(title=form.title.data, body=form.body.data, owned_user=current_user)
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
        post.body = form.body.data
        db.session.commit()
        flash('Post updated successfully!', category='success')
        return redirect(url_for('home_page'))
    elif request.method == 'GET':
        form.title.data = post.title
        form.body.data = post.body
    return render_template('edit_post.html', form=form)

@app.route('/delete_post/<int:post_id>', methods=['GET', 'POST'])
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