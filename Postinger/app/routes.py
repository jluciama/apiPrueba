from app import app, db, login_manager
from app.forms import RegisterForm, LoginForm, CreatePostForm, EditPostForm, ForgotPasswordForm, ProfileForm, AgeCheckForm
from app.models import User, Post
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
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
        flash("You are already logged in!", category='info')
        return redirect(url_for('home_page'))
    
    form = LoginForm()

    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user:
            if attempted_user.check_password(form.password.data):
                if attempted_user.status == 'deactivated':
                    return render_template('login.html', form=form, reactivate=True, user_id=attempted_user.id)
                else:
                    login_user(attempted_user)
                    flash(f'You are now logged in as: {attempted_user.username}', category='success')
                    return redirect(url_for('home_page'))
            else:
                flash('Incorrect password. Please try again.', category='danger')
        else:
            flash('User does not exist. Please check your username.', category='danger')
    
    return render_template('login.html', form=form)

@app.route('/reactivate_account', methods=['POST'])
def reactivate_account():
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    if user:
        user.reactivate()
        db.session.commit()
        flash('Your account has been reactivated. Welcome back!', category='success')
        login_user(user)
        return redirect(url_for('home_page'))
    else:
        flash('Failed to reactivate account. Please try again.', category='danger')
    return redirect(url_for('login_page'))


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
    
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

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
            user.name = username
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('home_page'))
        except Exception as e:
            flash('An unexpected error occurred. Please try again later.', 'danger')
            app.logger.error(f"Error while registering user: {str(e)}")
            return render_template('register.html', form=form)

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return render_template('register.html', form=form)


@app.route('/age-check', methods=['GET', 'POST'])
def age_check_page():
    form = AgeCheckForm()
    if form.validate_on_submit():
        date_of_birth = form.date_of_birth.data
        today = datetime.now().date()

        if date_of_birth > today:
            flash("Please enter a valid date of birth.", category='danger')
        else:
            provided_age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

            if provided_age < 18:
                flash("You must be 18 or older to join our network!", category='danger')
            elif provided_age >= 100:
                flash("You must be younger than 100 years old to join our network!", category='danger')
            else:
                flash("Welcome! Please register.", category='info')
                return redirect(url_for('register_page'))

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return render_template('age_check.html', form=form, current_datetime=datetime.now())


@app.route('/home', methods=['GET'])
@login_required
def home_page():
    create_post_form = CreatePostForm()
    edit_post_form = EditPostForm()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # Default to 10 entries per page

    search_query = request.args.get('search', '')
    tag_search = request.args.get('tag_search', '')

    order_by = request.args.get('order_by', 'date')
    order_direction = request.args.get('order_direction', 'desc')  # Default to descending order

    posts_query = Post.query

    if search_query:
        posts_query = posts_query.filter(or_(Post.title.contains(search_query), Post.body.contains(search_query)))

    if tag_search:
        if tag_search.startswith('#'):
            tag_search = tag_search[1:]

        tag_search_lower = tag_search.lower()
        posts_query = posts_query.filter(
            or_(
                func.lower(Post.tags).like(f'%,{tag_search_lower},%'),
                func.lower(Post.tags).like(f'{tag_search_lower},%'),
                func.lower(Post.tags).like(f'%,{tag_search_lower}'),
                func.lower(Post.tags).like(f'%{tag_search_lower}%')
            )
        )

    if order_by == 'date':
        posts_query = posts_query.order_by(Post.created_at.desc() if order_direction == 'desc' else Post.created_at.asc())
    elif order_by == 'likes':
        posts_query = posts_query.order_by(Post.likes_count.desc() if order_direction == 'desc' else Post.likes_count.asc())
    elif order_by == 'dislikes':
        posts_query = posts_query.order_by(Post.dislikes_count.desc() if order_direction == 'desc' else Post.dislikes_count.asc())

    posts = posts_query.paginate(page=page, per_page=per_page)

    return render_template('home.html', posts=posts, create_post_form=create_post_form, 
                           edit_post_form=edit_post_form,
                           order_by=order_by, order_direction=order_direction,
                           search_query=search_query, tag_search=tag_search, user=current_user)


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
        new_post.tags = ','.join(tags)

        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully!', category='success')
        return redirect(url_for('home_page'))
    return render_template('create_post.html', form=form, user=current_user)


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owned_user != current_user and not current_user.is_admin:
        abort(403)
    form = EditPostForm(obj=post)
    if form.validate_on_submit():
        form.populate_obj(post)
        
        if form.tags.data:
            tags = [tag.strip() for tag in form.tags.data.split('#') if tag.strip()]
            post.tags = ','.join(tags)
        
        db.session.commit()
        flash('Post updated successfully!', category='success')
        return redirect(url_for('home_page'))
    return render_template('edit_post.html', form=form, user=current_user)


@app.route('/delete_post/<int:post_id>', methods=['POST', 'DELETE'])
@login_required
def delete_post(post_id):
    if request.method in ['POST', 'DELETE']:
        post = Post.query.get_or_404(post_id)
        if not current_user.is_admin and post.owned_user != current_user:
            abort(403)
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully!', category='success')
        return redirect(url_for('home_page'))
    else:
        abort(405)


@app.route('/like_post', methods=['POST'])
@login_required
def like_post():
    post_id = request.form.get('post_id')
    post = Post.query.get_or_404(post_id)
    user = current_user

    if user in post.liked_users:
        post.likes_count -= 1
        post.liked_users.remove(user)
        db.session.commit()
        flash('You unliked the post.', 'info')
    else:
        if user in post.disliked_users:
            post.dislikes_count -= 1
            post.disliked_users.remove(user)
        post.likes_count += 1
        post.liked_users.append(user)
        db.session.commit()
        flash('You liked the post!', 'success')

    return redirect(request.referrer)


@app.route('/dislike_post', methods=['POST'])
@login_required
def dislike_post():
    post_id = request.form.get('post_id')
    post = Post.query.get_or_404(post_id)
    user = current_user

    if user in post.disliked_users:
        post.dislikes_count -= 1
        post.disliked_users.remove(user)
        db.session.commit()
        flash('You removed your dislike.', 'info')
    else:
        if user in post.liked_users:
            post.likes_count -= 1
            post.liked_users.remove(user)
        post.dislikes_count += 1
        post.disliked_users.append(user)
        db.session.commit()
        flash('You disliked the post!', 'warning')

    return redirect(request.referrer)


@app.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def profile_page(username):
    user_to_edit = User.query.filter_by(username=username).first_or_404()

    can_edit = False
    can_delete = False
    
    form = ProfileForm(obj=user_to_edit)
    
    if form.validate_on_submit() and (current_user == user_to_edit or current_user.is_admin):
        if User.query.filter_by(username=form.username.data).first() and form.username.data != user_to_edit.username:
            flash('Username already exists and belongs to another user', 'danger')
        else:
            form.populate_obj(user_to_edit)
            db.session.commit()
            flash('Profile updated successfully!', category='success')
            return redirect(url_for('home_page'))

    is_own_profile = (user_to_edit == current_user)
    can_delete = (current_user.is_admin and not is_own_profile) or (not current_user.is_admin and is_own_profile)
    can_edit = is_own_profile or current_user.is_admin

    return render_template('profile.html', user=user_to_edit, form=form, can_edit=can_edit, can_delete=can_delete)


@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    action = request.form.get('action')
    username = request.form.get('username')
    
    if action not in ['delete', 'deactivate']:
        flash('Invalid action requested.', 'danger')
        return redirect(url_for('home_page'))
    
    if action == 'delete':
        if current_user.is_admin:
            user_to_delete = User.query.filter_by(username=username).first()

            if not user_to_delete:
                flash('User not found!', 'danger')
                return redirect(url_for('home_page'))

            if user_to_delete.is_admin:
                flash('You cannot delete an admin account!', 'danger')
                return redirect(url_for('home_page'))

            db.session.delete(user_to_delete)
            db.session.commit()  # Commit the deletion
            flash(f'{user_to_delete.username}\'s account was successfully deleted!', 'success')
        else:
            if current_user.username != username:
                flash('You do not have enough privileges to delete another user\'s account!', 'danger')
                return redirect(url_for('home_page'))

            db.session.delete(current_user)
            db.session.commit()
            flash('Your account has been successfully deleted.', 'success')
            logout_user()
    elif action == 'deactivate':
        user_to_deactivate = User.query.filter_by(username=username).first()

        if not user_to_deactivate:
            flash('User not found!', 'danger')
            return redirect(url_for('home_page'))

        if current_user.username != username:
            flash('You do not have enough privileges to deactivate another user\'s account!', 'danger')
            return redirect(url_for('home_page'))

        user_to_deactivate.status = 'deactivated'
        db.session.commit()
        flash('User account has been deactivated.', 'info')

        if current_user == user_to_deactivate:
            logout_user()

    return redirect(url_for('login_page'))


@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("login_page"))