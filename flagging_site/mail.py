import io
import traceback
from functools import wraps

from flask import render_template
from flask import current_app
from flask_mail import Mail as _Mail
from flask_mail import Message


class Mail(_Mail):

    @wraps(_Mail.send)
    def send(self, message):
        # Only use this in staging and production.
        if current_app.env not in ['production', 'staging']:
            return
        super().send(message)


mail = Mail()


class ErrorEmail(Message):

    @wraps(Message.__init__)
    def __init__(self, **kwargs):
        recipients = [
            i.strip() for i in current_app.config['MAIL_ERROR_ALERTS_TO'].split(';')
        ]
        kwargs.setdefault('subject', 'Flagging site error')
        kwargs.setdefault('recipients', recipients)
        kwargs.setdefault('sender', current_app.config['MAIL_USERNAME'])
        super().__init__(**kwargs)


def mail_on_fail(template_name: str):
    """Send an email when something fails. Use this as a decorator."""
    def decorator(func: callable):
        @wraps(func)
        def _wrap(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                # Get the stack trace
                f = io.StringIO()
                traceback.print_exc(file=f)
                f.seek(0)

                # Send the email
                html = render_template(template_name, stack_trace=f.read())
                msg = ErrorEmail(html=html)
                mail.send(msg)

                # Raise the error
                raise
        return _wrap
    return decorator
