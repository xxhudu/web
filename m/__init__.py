import re
from webob import Request, Response
from webob import exc
from webob.dec import wsgify


_PATTERNS = {
    'str': r'[^/]+',
    'word': r'\w+',
    'int': r'[+-]?\d+',
    'float': r'[+-]?\d+\.\d+',
    'any': r'.+'
}

_TRANSLATORS = {
    'str': str,
    'word': str,
    'any': str,
    'int': int,
    'float': float
}


class _Context(dict):
    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)


class _AppContext(_Context):
    pass


class _RouterContext(_Context):
    app_ctx = None

    def with_app(self, app_ctx):
        self.app_ctx = app_ctx

    def __getattr__(self, item):
        if item in self.keys():
            return self[item]
        return getattr(self.app_ctx, item)

    def __setattr__(self, key, value):
        self[key] = value



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


class _Route:
    __slots__ = ['methods', 'pattern', 'translator', 'handler']

    def __init__(self, pattern, translator, methods, handler):
        self.pattern = re.compile(pattern)
        if translator is None:
            translator = {}
        self.translator = translator
        self.methods = methods
        self.handler = handler

    def run(self, prefix: str, ctx: _Context, request: Request):
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
            return self.handler(ctx, request)


class _Router:
    def __init__(self, prefix='', **kwargs):
        self.__prefix = prefix.rstrip('/')
        self._routes = []
        self._before_filters = []
        self._after_filters = []
        self._ctx = _RouterContext(kwargs)

    def context(self, ctx=None):
        if ctx:
            self._ctx.with_app(ctx)
        self._ctx.router = self
        return self._ctx

    @property
    def prefix(self):
        return self.__prefix

    def _rule_parse(self, rule: str, methods, handler) -> _Route:
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
        return _Route(''.join(pattern), translator, methods, handler)

    @staticmethod
    def _spec_parse(spec: str):
        name, _, type = spec.partition(':')
        if not name.isidentifier():
            raise Exception('name {} is not identifier'.format(name))
        if type not in _PATTERNS.keys():
            type = 'word'
        pattern = '(?P<{}>{})'.format(name, _PATTERNS[type])
        return name, pattern, _TRANSLATORS[type]

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
        self._before_filters.append(fn)
        return fn

    def after_request(self, fn):
        self._after_filters.append(fn)
        return

    def run(self, request: Request):
        if not request.path.startswith(self.prefix):
            return
        for fn in self._before_filters:
            request = fn(self._ctx, request)
        for route in self._routes:
            res = route.run(self.prefix, self._ctx, request)
            if res:
                for fn in self._after_filters:
                    res = fn(self._ctx, request, res)
                return res


class M:
    Router = _Router
    Request = Request
    Response = Response

    _routers = []
    _before_filters = []
    _after_filters = []
    _ctx = _AppContext()

    def __init__(self, **kwargs):
        self._ctx.app = self
        for k, v in kwargs.items():
            self._ctx[k] = v

    @classmethod
    def add_extension(cls, name, extension):
        cls._ctx[name] = extension

    @classmethod
    def register(cls, router: _Router):
        router.context(cls._ctx)
        cls._routers.append(router)

    @classmethod
    def before_request(cls, fn):
        cls._before_filters.append(fn)
        return fn

    @classmethod
    def after_request(cls, fn):
        cls._after_filters.append(fn)
        return fn

    @wsgify
    def __call__(self, request: Request) -> Response:
        for fn in self._before_filters:
            request = fn(self._ctx, request)
        for router in self._routers:
            response = router.run(request)
            if response:
                for fn in self._after_filters:
                    response = fn(self._ctx, request, response)
                return response
        raise exc.HTTPNotFound('not found')
