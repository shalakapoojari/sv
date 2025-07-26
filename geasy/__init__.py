from flask import Blueprint

geasy_bp = Blueprint(
    'geasy_bp',
    __name__,
    template_folder='templates',
)
# This import registers the routes
from . import routes
