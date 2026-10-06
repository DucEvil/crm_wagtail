import os


SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
SQLALCHEMY_DATABASE_URI = os.environ["SUPERSET_METADATA_URI"]

WTF_CSRF_ENABLED = True
ENABLE_PROXY_FIX = True
SCARF_ANALYTICS = False

FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
}

# Keep development queries bounded. The analytics role is also read-only at
# PostgreSQL level, so this is defense in depth rather than the only control.
SQLLAB_TIMEOUT = 60
SUPERSET_WEBSERVER_TIMEOUT = 60
ROW_LIMIT = 50_000
