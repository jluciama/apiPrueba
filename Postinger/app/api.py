# api = routes = controllers. Es decir, lo que hace el usuario. 
# cuando le da a register en la pagina web (front), le lleva a la ruta /register (back)
# importamos todas las clases del final de repos

# @api.route('/register')
# class RegisterRoute():
#    async def get(self):
#        user = await user_repo.find_one() ESTE ES EL METODO DE REPOS
#        return self.json(user)

# Si el usuario no es admin e intenta borrar, saltar excepcion de permisos

from app import app, db, login_manager
from app.forms import RegisterForm, LoginForm, CreatePostForm, EditPostForm, ForgotPasswordForm, ProfileForm, AgeCheckForm
from app.models import User, Post
from app.forms import RegisterDTO, LoginDTO, ForgotPasswordDTO, CreatePostDTO, EditPostDTO, AgeCheckDTO, ProfileDTO
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from pydantic import ValidationError
from repos import user_repo
import re


@app.route('/')
def root():
    if current_user.is_authenticated:
        flash("You are already authenticated!", category='info')
        return redirect(url_for('home_page'))
    else:
        return redirect(url_for('login_page'))


@app.route('/login')
class LoginRoute():

    async def get(self):
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            user = await user_repo.findOne(username)
            if user:
                validUser = await user_repo.checkPassword(username, password)
                if validUser:
                    login_user(user)
                    flash(f'You are now logged in as: {user.username}', category='success')
                    return redirect(url_for('home_page'))
            flash('Error logging in. Please check your credentials and try again.', category='danger')
        
        return render_template('login.html')
    
    async def patch(self): # add patch logic to login html
        username = "" # change this to extract username from login form
        reactivated = await user_repo.reactivateAccount(username)
        if reactivated:
            flash('Your account has been reactivated. Welcome back!', category='success')
            return redirect(url_for('home_page'))


"""@app.route('/forgot_password')
class ForgotPasswordRoute():

    async def get(self):
        form = ForgotPasswordForm()
        if form.validate_on_submit():
            user = await user_repo.resetPassword()
                if user:
                    user.set_password(forgot_password_data.password1)
                    db.session.commit()
                    flash('Password has been reset successfully.', 'success')
                    return redirect(url_for('login_page'))
                else:
                    flash('User with provided credentials does not exist.', 'danger')
            except ValidationError as e:
                flash(str(e), 'danger')
        
        if form.errors:
            for _, errors in form.errors.items():
                for error in errors:
                    flash(error, 'danger')

        return render_template('forgot_password.html', form=form)"""