import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DEBUG = os.environ.get('DEBUG', True)

DATABASE_URI = os.environ.get(
    'DATABASE_URI', 'sqlite:///' + os.path.join(BASE_DIR, 'audit.db')
)
DEFAULT_CONTENT_MAX_SIZE_IN_MB = 200
MAX_CONTENT_LENGTH = int(
    os.environ.get('MAX_CONTENT_LENGTH', DEFAULT_CONTENT_MAX_SIZE_IN_MB * 1024 * 1024)
)

# this is a nasty setting, but it makes usage locally much easier
EVERY_ONE_IS_ADMIN = bool(int(os.environ.get('EVERY_ONE_IS_ADMIN', 0)))

ADMINS = os.environ.get('ADMINS')
if ADMINS:
    ADMINS = set([int(adm_id) for adm_id in ADMINS.split(',')])
else:
    ADMINS = []

# Override these (and anything else) in config_local.py or
# set environment variables accordingly.
OAUTH_KEY = os.environ.get('OAUTH_KEY', '')
OAUTH_SECRET = os.environ.get('OAUTH_SECRET', '')
SECRET_KEY = os.environ.get('SECRET_KEY', '')
MAPILLARY_CLIENT_ID = os.environ.get('MAPILLARY_CLIENT_ID', '')

try:
    from config_local import *
except ImportError:
    pass
