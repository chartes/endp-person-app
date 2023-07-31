"""
email.py
helper functions for sending emails and managing email templates.
"""

from flask import render_template
from flask_mail import Message

from ..config import settings

def send_mail(mail, subject, sender, recipients, text_body, html_body):
    """send an email with the given parameters"""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def send_password_reset_email(mail, user):
    """send an email to reset the password of the given user"""
    token = user.get_reset_password_token()
    send_mail(mail, subject='[e-NDP DB Administration] Réinitialisation du mot de passe',
              sender=str(settings.FLASK_MAIL_USERNAME),
              recipients=[user.email],
              text_body=render_template('admin/email/reset_password.txt',
                                        user=user,
                                        token=token),
              html_body=render_template('admin/email/reset_password.html',
                                        user=user,
                                        token=token)
              )