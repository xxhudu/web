from webob import Request, Response
from webob import exc
from webob.dec import wsgify


def hello(request: Request) -> Response:
    name = request.params.get("name", 'anonymous')
    response = Response()
    response.text = 'hello {}'.format(name)
    response.status_code = 200
    response.content_type = 'text/plain'
    return response


def index(request: Request) -> Response:
    return Response(body='hello world', content_type='text/plain')


router = {
    '/hello': hello,
    '/': index
}


class Application:
    ROUTER = {}

    @classmethod
    def register(cls, path, handler):
        cls.ROUTER[path] = handler

    @wsgify
    def __call__(self, request: Request) -> Response:
        try:
            return self.ROUTER[request.path](request)
        except KeyError:
            raise exc.HTTPNotFound('not found')

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    Application.register('/hello', hello)
    Application.register('/', index)

    server = make_server('0.0.0.0', 8000, Application())
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


# /hello?name=comyn => hello comyn
# / => hello world