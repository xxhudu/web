from functools import wraps
from webob import Request, Response


def wsgify(fn):
    @wraps(fn)
    def wrap(environ, start_response):
        request = Request(environ)
        response = fn(request)
        return response(environ, start_response)
    return wrap
