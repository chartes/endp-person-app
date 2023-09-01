import os
from api.config import (BASE_DIR,
                        settings)

from whoosh import index

WHOOSH_INDEX_DIR = os.path.join(BASE_DIR, settings.WHOOSH_INDEX_DIR)

# open index for full-text search
ix = None
if os.path.exists(WHOOSH_INDEX_DIR):
    ix = index.open_dir(WHOOSH_INDEX_DIR)