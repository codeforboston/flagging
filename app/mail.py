import io
import traceback
from functools import wraps
from typing import TypeVar

import pandas as pd
from flask import current_app
from flask import render_template
from flask_mail import Mail as _Mail
from flask_mail import Message


T = TypeVar("T")


class Mail(_Mail):
    def send(self, message: Message) -> None:
        # Only use this in staging and production.
        if not current_app.config["SEND_EMAILS"]:
            print("(Was about to send email, but did not because SEND_EMAILS=false.)")
            return
        super().send(message)


mail = Mail()


class ErrorEmail(Message):
    def __init__(self, **kwargs):
        recipients = current_app.config["MAIL_ERROR_ALERTS_TO"]
        kwargs.setdefault("subject", "Flagging site error")
        kwargs.setdefault("recipients", recipients)
        kwargs.setdefault("sender", current_app.config["MAIL_USERNAME"])
        super().__init__(**kwargs)


class ExportEmail(Message):
    def __init__(self, **kwargs):
        recipients = current_app.config["MAIL_DATABASE_EXPORTS_TO"]
        html = render_template("mail/periodic_data_delivery.html")
        kwargs.setdefault("html", html)
        kwargs.setdefault("subject", "Flagging site data exports")
        kwargs.setdefault("recipients", recipients)
        kwargs.setdefault("sender", current_app.config["MAIL_USERNAME"])
        super().__init__(**kwargs)

    def attach_dataframe(self, df: pd.DataFrame, filename: str) -> None:
        with io.StringIO() as f:
            df.to_csv(f, index=False)
            self.attach(filename, "text/csv", f.getvalue())


def mail_on_fail(func: T) -> T:
    """Send an email when something fails. Use this as a decorator."""

    @wraps(func)
    def _wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Handle recursive error handling.
            # This way if a task wrapped in `@mail_on_fail` sends an email, we
            # don't sent multiple emails.
            if getattr(e, "__email_sent__", False):
                raise e

            # Get the stack trace
            with io.StringIO() as f:
                traceback.print_exc(file=f)
                # Render the email body
                html = render_template(
                    "mail/error.html",
                    stack_trace=f.getvalue(),
                    func_name=getattr(func, "__name__", repr(func)),
                )

            # Send the email
            msg = ErrorEmail(html=html)
            mail.send(msg)

            # Mark as sent
            e.__email_sent__ = True

            # Raise the error
            raise e

    return _wrap
