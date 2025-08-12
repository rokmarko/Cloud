"""
Authentication routes
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from src.app import db, mail
from src.models import User
from src.forms import LoginForm, RegistrationForm, RequestPasswordResetForm, ResetPasswordForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash('Please verify your email address before logging in.', 'warning')
                return redirect(url_for('auth.login'))
            
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', title='Sign In', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            nickname=form.nickname.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(user)
        
        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address."""
    user = User.verify_token(token, 'email-verification', max_age=86400)  # 24 hours
    
    if not user:
        flash('Invalid or expired verification token.', 'danger')
        return redirect(url_for('auth.login'))
    
    user.is_verified = True
    user.is_active = True
    db.session.commit()
    
    flash('Your email has been verified! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/request-password-reset', methods=['GET', 'POST'])
def request_password_reset():
    """Request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/request_password_reset.html', title='Reset Password', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    user = User.verify_token(token, 'password-reset', max_age=3600)  # 1 hour
    
    if not user:
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.request_password_reset'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form)


def send_verification_email(user):
    """Send email verification email."""
    token = user.generate_verification_token()
    msg = Message(
        'KanardiaCloud - Verify Your Email',
        recipients=[user.email]
    )
    msg.body = f'''To verify your email address, click the following link:

{url_for('auth.verify_email', token=token, _external=True)}

If you did not register for this account, please ignore this email.

Best regards,
KanardiaCloud Team
'''
    msg.html = f'''
    <h2>Welcome to KanardiaCloud!</h2>
    <p>To verify your email address, click the button below:</p>
    <p><a href="{url_for('auth.verify_email', token=token, _external=True)}" 
         style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
         Verify Email
    </a></p>
    <p>If you did not register for this account, please ignore this email.</p>
    <p>Best regards,<br>KanardiaCloud Team</p>
    '''
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")


def send_password_reset_email(user):
    """Send password reset email."""
    token = user.generate_reset_token()
    msg = Message(
        'KanardiaCloud - Password Reset',
        recipients=[user.email]
    )
    msg.body = f'''To reset your password, click the following link:

{url_for('auth.reset_password', token=token, _external=True)}

If you did not request a password reset, please ignore this email.

Best regards,
KanardiaCloud Team
'''
    msg.html = f'''
    <h2>Password Reset Request</h2>
    <p>To reset your password, click the button below:</p>
    <p><a href="{url_for('auth.reset_password', token=token, _external=True)}" 
         style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
         Reset Password
    </a></p>
    <p>This link will expire in 1 hour.</p>
    <p>If you did not request a password reset, please ignore this email.</p>
    <p>Best regards,<br>KanardiaCloud Team</p>
    '''
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
