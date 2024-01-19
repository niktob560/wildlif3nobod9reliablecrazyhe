from aiohttp import web
from aiohttp.web_middlewares import middleware

from schema import ErrorResponse


@middleware
async def exc_handler(req: web.Request, handler):
    try:
        return await handler(req)
    except ErrorResponse as e:
        return e
