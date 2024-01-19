from aiohttp import web
from aiohttp.web_middlewares import middleware

from schema import ErrorResponse


@middleware
async def serializer(req: web.Request, handler):
    res = await handler(req)
    if isinstance(res, web.Response):
        return res
    if 'status' in dir(res):
        return web.json_response(res.to_json(), status=res.status)
    if req.method == 'DELETE':
        return web.Response(status=204)
    if req.method == 'POST':
        return web.Response(status=201)
    if isinstance(res, list):
        return web.json_response(list(map(lambda x: x.to_json(), res)))
    if not isinstance(res, str) and not isinstance(res, dict):
        res = res.to_json()
    return web.json_response(res)
