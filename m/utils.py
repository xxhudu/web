import json
from m import M


def jsonify(**kwargs):
    body = json.dumps(kwargs)
    return M.Response(body, content_type='application/json', charset='utf-8')
