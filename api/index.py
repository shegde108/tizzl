import sys
import os

# Add the tizzl directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tizzl'))

from tizzl.api.main import app
from mangum import Mangum

handler = Mangum(app)