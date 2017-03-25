def application(environ, start_response):
    # biz
    start_response('200 OK', [('Content-Type', 'text/plain')]) # headers
    return ["hello world".encode()] # body

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    server = make_server('0.0.0.0', 8000, application)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
