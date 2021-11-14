import io
import traceback
from functools import wraps

from flask import render_template
from flask import current_app
from flask_mail import Mail as _Mail
from flask_mail import Message


class Mail(_Mail):

    def send(self, message):
        # Only use this in staging and production.
        if current_app.env not in ['production', 'staging']:
            return
        super().send(message)


mail = Mail()


class ErrorEmail(Message):

    def __init__(self, **kwargs):
        recipients = [
            i.strip() for i in current_app.config['MAIL_ERROR_ALERTS_TO'].split(';')
        ]
        kwargs.setdefault('subject', 'Flagging site error')
        kwargs.setdefault('recipients', recipients)
        kwargs.setdefault('sender', current_app.config['MAIL_USERNAME'])
        super().__init__(**kwargs)


def mail_on_fail(func: callable):
    """Send an email when something fails. Use this as a decorator."""
    @wraps(func)
    def _wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Handle recursive error handling.
            # This way if a task wrapped in `@mail_on_fail` sends an email, we
            # don't sent multiple emails.
            if getattr(e, '__email_sent__', False):
                raise e

            # Get the stack trace
            f = io.StringIO()
            traceback.print_exc(file=f)
            f.seek(0)

            # Render the email body
            html = render_template(
                'mail/error.html',
                stack_trace=f.read(),
                func_name=getattr(func, '__name__', repr(func))
            )

            # Send the email
            msg = ErrorEmail(html=html)
            mail.send(msg)

            # Mark as sent
            e.__email_sent__ = True

            # Raise the error
            raise e
    return _wrap
