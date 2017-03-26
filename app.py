import re
from webob import Request, Response
from webob import exc
from webob.dec import wsgify


PATTERNS = {
    'str': r'[^/]+',
    'word': r'\w+',
    'int': r'[+-]?\d+',
    'float': r'[+-]?\d+\.\d+',
    'any': r'.+'
}

TRANSLATORS = {
    'str': str,
    'word': str,
    'any': str,
    'int': int,
    'float': float
}


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


class Route:
    __slots__ = ['methods', 'pattern', 'translator', 'handler']

    def __init__(self, pattern, translator, methods, handler):
        self.pattern = re.compile(pattern)
        if translator is None:
            translator = {}
        self.translator = translator
        self.methods = methods
        self.handler = handler

    def run(self, prefix: str, request: Request):
        if self.methods:
            if isinstance(self.methods, (list, tuple, set)) and request.method not in self.methods:
                return
            if isinstance(self.methods, str) and self.methods != request.method:
                return
        m = self.pattern.match(request.path.replace(prefix, '', 1))
        if m:
            vs = {}
            for k, v in m.groupdict().items():
                vs[k] = self.translator[k](v)
                # request.params.add(k, vs[k])
            request.vars = _Vars(vs)
            return self.handler(request)


class Router:
    def __init__(self, prefix=''):
        self.__prefix = prefix.rstrip('/')
        self._routes = []
        self.before_filters = []
        self.after_filters = []

    @property
    def prefix(self):
        return self.__prefix

    def _rule_parse(self, rule: str, methods, handler) -> Route:
        pattern = ['^']
        spec = []
        translator = {}
        # /home/{name:str}/{id:int}   ^/home/(?P<name>[^/]+)/(?P<id>[+-]?\d+)$
        is_spec = False
        for c in rule:
            if c == '{':
                is_spec = True
            elif c == '}':
                is_spec = False
                name, pat, t = self._spec_parse(''.join(spec))
                pattern.append(pat)
                translator[name] = t
                spec.clear()
            elif is_spec:
                spec.append(c)
            else:
                pattern.append(c)
        pattern.append('$')
        return Route(''.join(pattern), translator, methods, handler)

    @staticmethod
    def _spec_parse(spec: str):
        name, _, type = spec.partition(':')
        if not name.isidentifier():
            raise Exception('name {} is not identifier'.format(name))
        if type not in PATTERNS.keys():
            type = 'word'
        pattern = '(?P<{}>{})'.format(name, PATTERNS[type])
        return name, pattern, TRANSLATORS[type]

    def route(self, rule, methods=None):
        def wrap(handler):
            route = self._rule_parse(rule, methods, handler)
            self._routes.append(route)
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

    def before_request(self, fn):
        self.before_filters.append(fn)
        return fn

    def after_request(self, fn):
        self.after_filters.append(fn)
        return

    def run(self, request: Request):
        if not request.path.startswith(self.prefix):
            return
        for fn in self.before_filters:
            request = fn(self, request)
        for route in self._routes:
            res = route.run(self.prefix, request)
            if res:
                for fn in self.after_filters:
                    res = fn(self, request, res)
                return res


class Application:
    ROUTERS = []
    before_filters = []
    after_filters = []

    @classmethod
    def register(cls, router: Router):
        cls.ROUTERS.append(router)

    @classmethod
    def before_request(cls, fn):
        cls.before_filters.append(fn)
        return fn

    @classmethod
    def after_request(cls, fn):
        cls.after_filters.append(fn)
        return fn

    @wsgify
    def __call__(self, request: Request) -> Response:
        for fn in self.before_filters:
            request = fn(self, request)
        for router in self.ROUTERS:
            response = router.run(request)
            if response:
                for fn in self.after_filters:
                    response = fn(self, request, response)
                return response
        raise exc.HTTPNotFound('not found')


shop = Router('/shop')


@shop.get('/{id:int}')
def get_product(request: Request):
    print(request.vars.id)
    print(type(request.vars.id))
    return Response(body='product {}'.format(request.vars.id), content_type='text/plain')


@Application.before_request
def print_headers(app, request: Request):
    for k in request.headers.keys():
        print('{} => {}'.format(k, request.headers[k]))
    return request


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

# /home/{name:str}/{id:int}  str, word(\w+), int, float, any  request.vars request.params path > qs