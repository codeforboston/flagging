__version__ = '0.1.0'

# flask's CLI will automatically search for a Callable named "create_app"
# see https://github.com/pallets/flask/blob/master/src/flask/cli.py
from .app import create_app
