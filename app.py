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


class Router:
    def __init__(self, prefix=''):
        self.__prefix = prefix.rstrip('/')
        self._routes = []

    @property
    def prefix(self):
        return self.__prefix

    def route(self, pattern='.*', methods=None):
        def wrap(handler):
            self._routes.append((methods, re.compile(pattern), handler))
            return handler
        return wrap

    def get(self, pattern='.*'):
        return self.route(pattern, 'GET')

    def put(self, pattern='.*'):
        return self.route(pattern, 'PUT')

    def post(self, pattern='.*'):
        return self.route(pattern, 'POST')

    def delete(self, pattern='.*'):
        return self.route(pattern, 'DELETE')

    def patch(self, pattern='.*'):
        return self.route(pattern, 'PATCH')

    def head(self, pattern='.*'):
        return self.route(pattern, 'HEAD')

    def options(self, pattern='.*'):
        return self.route(pattern, 'OPTIONS')

    def run(self, request: Request):
        if not request.path.startswith(self.prefix):
            return
        for methods, pattern, handler in self._routes:
            if methods:
                if isinstance(methods, (list, tuple, set)) and request.method not in methods:
                    continue
                if isinstance(methods, str) and methods != request.method:
                    continue
            m = pattern.match(request.path.replace(self.prefix, '', 1))
            if m:
                request.args = m.groups()
                request.kwargs = _Vars(m.groupdict())
                return handler(request)


class Application:
    ROUTERS = []

    @classmethod
    def register(cls, router: Router):
        cls.ROUTERS.append(router)

    @wsgify
    def __call__(self, request: Request) -> Response:
        for router in self.ROUTERS:
            response = router.run(request)
            if response:
                return response
        raise exc.HTTPNotFound('not found')


shop = Router('/shop')


@shop.get(r'^/(?P<id>\d+)$')
def get_product(request: Request):
    print(request.kwargs.id)
    return Response(body='product {}'.format(request.kwargs.id), content_type='text/plain')


Application.register(router=shop)


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

# shop = Router('/shop')
# shop.get('/(?P<id>\d+)') = /shop/12345