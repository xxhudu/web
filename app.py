from urllib.parse import parse_qs


def application(environ: dict, start_response):
    params = parse_qs(environ['QUERY_STRING'])
    name = params.get('name', ['anonymous'])[0]
    start_response('200 OK', [('Content-Type', 'text/plain')]) # headers
    return ["hello {}".format(name).encode()] # body

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    server = make_server('0.0.0.0', 8000, application)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
