from app import app, db, login_manager
from flask import render_template, redirect, url_for, flash, request, abort
from app.models import User, Post
from app.forms import RegisterForm, LoginForm, CreatePostForm, EditPostForm, DeletePostForm, ForgotPasswordForm
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, func

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

    search_query = request.args.get('search', '')
    tag_search = request.args.get('tag_search', '')

    if search_query and tag_search:
        # If both search and tag_search parameters are provided, search by both
        posts = Post.query.filter(or_(Post.title.contains(search_query), 
                                      Post.body.contains(search_query),
                                      Post.tags.like(f"%{tag_search}%"))) \
            .paginate(page=page, per_page=per_page)
    elif search_query:
        # If only search parameter is provided, search normally
        posts = Post.query.filter(or_(Post.title.contains(search_query), 
                                      Post.body.contains(search_query))) \
            .paginate(page=page, per_page=per_page)
    elif tag_search:
        # If only tag_search parameter is provided, search by tag
        posts = Post.query.filter(Post.tags.like(f"%{tag_search}%")).paginate(page=page, per_page=per_page)
    else:
        # If neither search nor tag_search parameter is provided, fetch all posts
        posts = Post.query.paginate(page=page, per_page=per_page)

    return render_template('home.html', posts=posts, create_post_form=create_post_form, 
                           edit_post_form=edit_post_form, delete_post_form=delete_post_form)

@app.route('/search_by_tag/<tag_name>')
def search_by_tag(tag_name):
    posts = Post.query.filter(Post.tags.any(tag_name)).paginate(page=1, per_page=10)
    return render_template('home.html', posts=posts)

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = Post(
            title=form.title.data,
            body=form.body.data,
            owned_user=current_user
        )
        tags = [tag.strip() for tag in form.tags.data.split('#') if tag.strip()]
        new_post.tags = ','.join(tags)  # Convert list of tags to a comma-separated string

        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully!', category='success')
        return redirect(url_for('home_page'))
    return render_template('create_post.html', form=form)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owned_user != current_user:
        abort(403)
    form = EditPostForm(obj=post)
    if form.validate_on_submit():
        form.populate_obj(post)
        if form.tags.data:
            post.tags.clear()
            tags = form.tags.data.split(',')
            for tag in tags:
                post.tags.append(tag.strip())
        db.session.commit()
        flash('Post updated successfully!', category='success')
        return redirect(url_for('home_page'))
    return render_template('edit_post.html', form=form)

@app.route('/delete_post/<int:post_id>', methods=['POST', 'DELETE'])
@login_required
def delete_post(post_id):
    if request.method in ['POST', 'DELETE']:
        post = Post.query.get_or_404(post_id)
        if post.owned_user != current_user:
            abort(403)
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully!', category='success')
        return redirect(url_for('home_page'))
    else:
        abort(405)  # Method Not Allowed


@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("login_page"))