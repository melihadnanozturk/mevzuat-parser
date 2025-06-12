"""
Legal Parser Blueprint for Microservice Integration
"""

from flask import Blueprint

# Blueprint oluşturma
legal_parser = Blueprint(
    'legal_parser', 
    __name__, 
    template_folder='templates',
    static_folder='static',
    static_url_path='/legal-parser/static',
    url_prefix='/legal-parser'
)

# Routes'ları import et
from . import routes