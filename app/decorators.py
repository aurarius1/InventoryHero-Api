from functools import wraps
from flask import session


def authorize(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if not session.get("username", None):
            return {}, 401
        return f(*args, **kwargs)
    return decorator
