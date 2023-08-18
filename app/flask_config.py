import os


class Config(object):
    SQLALCHEMY_DATABASE_URI = \
        os.getenv("DATABASE_URI", "") or os.getenv("DATABASE_CONNECTION", "") or "sqlite:///:memory:"

    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("sqlite", "sqlite+pysqlite")

    SESSION_PERMANENT = False
    SESSION_TYPE = os.getenv("SESSION_STORAGE", "filesystem")
    SECRET_KEY = os.getenv("SECRET", "SUPER_SECRET_KEY")


class DebugConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False


def get_config():
    is_development = eval(os.environ.get("IS_DEVELOPMENT", "False").capitalize())
    if is_development:
        return DebugConfig
    return ProdConfig
