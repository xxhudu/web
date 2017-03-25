import re
from webob import Request, Response
from webob import exc
from webob.dec import wsgify


class _Vars:
    def __init__(self, data=None):
        if data is not None:
            self._data = data
        else:
            self._data = {}

    def __getattr__(self, item):
        try:
            return self._data[item]
        except KeyError:
            raise AttributeError('no attribute {}'.format(item))

    def __setattr__(self, key, value):
        if key != '_data':
            raise NotImplemented
        self.__dict__['_data'] = value


class Application:
    ROUTER = []

    @classmethod
    def route(cls, methods=None, pattern='.*'):
        def wrap(handler):
            cls.ROUTER.append((methods, re.compile(pattern), handler))
            return handler
        return wrap

    @classmethod
    def get(cls, pattern):
        return cls.route('GET', pattern)

    @classmethod
    def put(cls, pattern):
        return cls.route('PUT', pattern)

    @classmethod
    def post(cls, pattern):
        return cls.route('POST', pattern)

    @classmethod
    def delete(cls, pattern):
        return cls.route('DELETE', pattern)

    @classmethod
    def head(cls, pattern):
        return cls.route('HEAD', pattern)

    @classmethod
    def options(cls, pattern):
        return cls.route('OPTIONS', pattern)

    @wsgify
    def __call__(self, request: Request) -> Response:
        for methods, pattern, handler in self.ROUTER:
            if methods:
                if isinstance(methods, (list, tuple, set)) and request.method not in methods:
                    continue
                if isinstance(methods, str) and methods != request.method:
                    continue
            m = pattern.match(request.path)
            if m:
                request.args = m.groups()
                request.kwargs = _Vars(m.groupdict())
                return handler(request)
        raise exc.HTTPNotFound('not found')


@Application.get('^/hello/(?P<name>\w+)$')
def hello(request: Request) -> Response:
    # name = request.params.get("name", 'anonymous')
    name = request.kwargs.name
    response = Response()
    response.text = 'hello {}'.format(name)
    response.status_code = 200
    response.content_type = 'text/plain'
    return response


@Application.route(methods=('GET', 'PUT'), pattern='^/$')
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
# /hello/(\w+)  request.args[0]
# /hello/(?P<name>\w+)  request.kwargs.name
# @get('/hello/(?P<name>\w+)')