from flask import Flask
from flask import Response
from flask_basicauth import BasicAuth
from werkzeug.exceptions import HTTPException


basic_auth = BasicAuth()

def init_auth(app: Flask):
    with app.app_context():
        basic_auth.init_app(app)

# Taken from https://computableverse.com/blog/flask-admin-using-basicauth
class AuthException(HTTPException):
    def __init__(self, message):
        """HTTP Forbidden error that prompts for login"""
        super().__init__(message, Response(
            'You could not be authenticated. Please refresh the page.',
            status=401,
            headers={'WWW-Authenticate': 'Basic realm="Login Required"'}
        ))
