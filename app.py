import webob
from webob.dec import wsgify


@wsgify
def application(request: webob.Request) -> webob.Response:
    name = request.params.get("name", 'anonymous')

    response = webob.Response()
    response.text = 'hello {}'.format(name)
    response.status_code = 200
    response.content_type = 'text/plain'
    return response

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    server = make_server('0.0.0.0', 8000, application)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
