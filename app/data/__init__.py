# flake8: noqa
""""
The data module contains exactly what you'd expect: everything related to data
processing, collection, and storage.
"""
from .database import db

# Register to metadata.
from .models import _all
