import sys
import os

# Adding this so that there is no need to install either library, just have them in the same folder.
__root_location__ = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(__root_location__, '..'))

from app import app
if 'PORT' in os.environ:
    post = os.environ['PORT']
else:
    port = 8000

app.run(host="0.0.0.0", port=port)
