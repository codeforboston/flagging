from flask_basicauth import BasicAuth as _BasicAuth
from werkzeug.exceptions import abort


class BasicAuth(_BasicAuth):
    """Uses HTTP BasicAuth to authenticate the admin user. We subclass the
    original object to add a convenient method, `get_login`, that handles both
    authentication and logging in (in conjunction with our error handler for 401
    responses.
    """

    def get_login(self):
        """Check if properly authenticated. If not, then return a 401 error.
        The 401 error page will in turn prompt the user for a username and
        password.
        """
        if not self.authenticate():
            abort(401)


basic_auth = BasicAuth()
