from webob import Request, Response
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


@wsgify
def application(request: Request) -> Response:
    return router.get(request.path, index)(request)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    server = make_server('0.0.0.0', 8000, application)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


# /hello?name=comyn => hello comyn
# / => hello world