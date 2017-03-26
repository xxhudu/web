from m import M
import json


def jsonify(**kwargs):
    body = json.dumps(kwargs)
    return M.Response(body, content_type='application/json', charset='utf-8')



shop = M.Router('/shop')


@shop.get('/{id:int}')
def get_product(ctx, request):
    return jsonify(id=request.vars.id)


if __name__ == '__main__':
    app = M()
    app.register(shop)
    from wsgiref.simple_server import make_server
    server = make_server('0.0.0.0', 8000, app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()