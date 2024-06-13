from flask import Blueprint, render_template, url_for, flash, redirect, request, g
from flask_login import login_user, current_user, logout_user, login_required, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector.errors
from project.utils import mail
import secrets

authentication_bp = Blueprint('authentication', __name__)

class User(UserMixin):
    def __init__(self, id, email, username, password):
        self.id = id
        self.email = email
        self.username = username
        self.password = password

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                           validators=[
                               DataRequired(), 
                               Length(min=8, max=20, message='Username must be between 8 and 20 characters'),
                               Regexp(r'^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9]+$', 
                                      message='Username must contain at least one letter and one number')
                           ])
    email = StringField('Email', 
                        validators=[
                            DataRequired(), 
                            Email()
                        ])
    password = PasswordField('Password', 
                             validators=[
                                 DataRequired(), 
                                 Length(min=8, message='Password must be at least 8 characters long'),
                                 Regexp('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[@$!%*?&])', 
                                        message='Password must contain at least one lowercase letter, one uppercase letter, one digit, and one special character')
                             ])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[
                                         DataRequired(), 
                                         EqualTo('password', message='Passwords must match')
                                     ])
    submit = SubmitField('Sign Up')

from flask_login import current_user

@authentication_bp.route("/")
def home():
    cursor = g.db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tbl_recipes')
    recipes = cursor.fetchall()
    cursor.close()
    
    return render_template('auth/index.html', recipes=recipes)


@authentication_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('authentication.home'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        cursor = g.db.cursor()
        cursor.execute('SELECT id, email, username, password FROM tbl_users WHERE email = %s', (form.email.data,))
        user = cursor.fetchone()
        
        if user:
            flash('User with this email already registered. Please use a different email.', 'danger')
        else:
            try:
                pwh_hash = generate_password_hash(form.password.data)
                cursor.execute('INSERT INTO tbl_users (username, email, password) VALUES (%s, %s, %s)', 
                               (form.username.data, form.email.data, pwh_hash))
                g.db.commit()
                flash('Your account has been created! You are now able to log in', 'success')
                return redirect(url_for('authentication.login'))
            except mysql.connector.errors.IntegrityError as err:
                if err.errno == 1062:  # Duplicate entry error code
                    flash('The username is already taken. Please choose a different username.', 'danger')
                else:
                    flash('An error occurred. Please try again later.', 'danger')
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return render_template('auth/register.html', title='Register', form=form)


# Define the login form within the route file
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@authentication_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('authentication.home'))
    form = LoginForm()
    if form.validate_on_submit():
        cursor = g.db.cursor()
        cursor.execute('SELECT id, email, username, password FROM tbl_users WHERE email = %s', (form.email.data,))
        user = cursor.fetchone()
        
        if user:
            check_pass = check_password_hash(
                user[3], form.password.data)
            if check_pass:
                user_obj = User(user[0], user[1], user[2], user[3])
                login_user(user_obj)
                return redirect(url_for('authentication.home'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@authentication_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('authentication.home'))


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', 
                                     validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

@authentication_bp.route("/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        cursor = g.db.cursor()
        cursor.execute('SELECT password FROM tbl_users WHERE id = %s', (current_user.id,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[0], form.old_password.data):
            new_password_hash = generate_password_hash(form.new_password.data)
            try:
                cursor.execute('UPDATE tbl_users SET password = %s WHERE id = %s', (new_password_hash, current_user.id))
                g.db.commit()
                flash('Your password has been updated!', 'success')
                return redirect(url_for('authentication.home'))
            except mysql.connector.errors.IntegrityError:
                flash('An error occurred. Please try again later.', 'danger')
        else:
            flash('Incorrect old password.', 'danger')
    
    return render_template('auth/change_password.html', title='Change Password', form=form)

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')

@authentication_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        # Check if the email exists in the database
        cursor = g.db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM tbl_users WHERE email = %s', (form.email.data,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            # Generate a unique token for password reset
            token = secrets.token_urlsafe(16)
            
            # Store the token in the database for the user
            cursor = g.db.cursor()
            cursor.execute('UPDATE tbl_users SET reset_token = %s WHERE email = %s', (token, form.email.data))
            g.db.commit()
            cursor.close()
            
            # Send reset password email using your user_mail function
            title = 'Password Reset Request'
            body = f'''
                To reset your password, visit the following link:
                {url_for('authentication.reset_password', token=token, _external=True)}
                
                If you did not make this request, simply ignore this email and no changes will be made.
                '''
            mail.user_mail(title, body, form.email.data)
            
            flash('An email with instructions to reset your password has been sent.', 'success')
            return redirect(url_for('authentication.login'))
        else:
            flash('Email not found. Please enter a valid email address.', 'danger')
    
    return render_template('auth/forgot_password.html', form=form)

# Define the form for resetting the password
class PasswordResetForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Reset Password')

@authentication_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        # Check if the token matches the one stored in the database for the user
        cursor = g.db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM tbl_users WHERE reset_token = %s', (token,))
        user = cursor.fetchone()
        
        if user:
            # Update the user's password and clear the reset_token
            new_password_hash = generate_password_hash(form.new_password.data)
            cursor.execute('UPDATE tbl_users SET password = %s, reset_token = NULL WHERE id = %s', (new_password_hash, user['id']))
            g.db.commit()
            cursor.close()

            flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
            return redirect(url_for('authentication.login'))
        else:
            flash('Invalid or expired token. Please try again.', 'danger')
    
    return render_template('auth/reset_password.html', form=form)