import re
from webob import Request, Response
from webob import exc
from webob.dec import wsgify


class Application:
    ROUTER = []

    @classmethod
    def register(cls, pattern):
        def wrap(handler):
            cls.ROUTER.append((re.compile(pattern), handler))
            return handler
        return wrap

    @wsgify
    def __call__(self, request: Request) -> Response:
        for pattern, handler in self.ROUTER:
            if pattern.match(request.path):
                return handler(request)
        raise exc.HTTPNotFound('not found')


@Application.register('^/hello$')
def hello(request: Request) -> Response:
    name = request.params.get("name", 'anonymous')
    response = Response()
    response.text = 'hello {}'.format(name)
    response.status_code = 200
    response.content_type = 'text/plain'
    return response


@Application.register('^/$')
def index(request: Request) -> Response:
    return Response(body='hello world', content_type='text/plain')

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    server = make_server('0.0.0.0', 8000, Application())
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


# /hello?name=comyn => hello comyn
# / => hello world