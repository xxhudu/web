from m import M
from m.utils import jsonify

shop = M.Router('/shop')


@shop.get('/{id:int}')
def get_product(ctx, request):
    print(ctx.test)
    return jsonify(id=request.vars.id)


if __name__ == '__main__':
    app = M()
    app.register(shop)
    app.add_extension('test', 'test')
    from wsgiref.simple_server import make_server

    server = make_server('0.0.0.0', 8000, app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
