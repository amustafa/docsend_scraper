import sys
import os

# Adding this so that there is no need to install either library, just have them in the same folder.
__root_location__ = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(__root_location__, '..'))

from app import app
app.run(host="0.0.0.0", debug=True, port=8000)
