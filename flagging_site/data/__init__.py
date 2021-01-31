"""
The data module contains exactly what you'd expect: everything related to data
processing, collection, and storage.
"""
from .database import db

# SqlAlchemy database models
db.metadata.clear()
from .boathouses import Boathouse
from .live_website_options import LiveWebsiteOptions
