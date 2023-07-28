"""
routes.py

Specific routes for the admin blueprint
"""

from flask import render_template, flash, redirect, url_for
from flask_login import current_user

from ..models import User
from ..database import session
from . import flask_app, mail
from .email import send_password_reset_email
from .forms import ResetPasswordRequestForm, ResetPasswordForm


@flask_app.route('/reset_password_request', methods=('GET', 'POST'))
def reset_password_request():
    """request a password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = session.query(User).filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(mail, user)
        flash('Vérifiez votre boîte mail pour obtenir les instructions de réinitialisation du mot de passe.')
        return redirect(url_for('admin.login'))
    return render_template('admin/reset_password_request.html', form=form)


@flask_app.route('/reset_password/<token>', methods=('GET', 'POST'))
def reset_password(token):
    """reset the password"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('admin.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        session.commit()
        flash('Votre mot de passe a été réinitialisé.')
        return redirect(url_for('admin.login'))
    return render_template('admin/reset_password.html', form=form, user=user)