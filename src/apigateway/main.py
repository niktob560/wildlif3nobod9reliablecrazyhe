# This is a sample Python script.
from dataclasses import dataclass
from typing import Optional, Any

from aiohttp import web

import exc_handler
import route
import serializer
from handlers import *

if __name__ == '__main__':
    app = web.Application(middlewares=[])

    api_app = web.Application(middlewares=[serializer.serializer, exc_handler.exc_handler])
    api_app.router.add_routes(routes)
    app.add_subapp('/api/v1/', api_app)

    manage_routes = web.RouteTableDef()


    @manage_routes.get('/manage/health')
    async def healthcheck(r):
        return aiohttp.web.Response(status=200)


    app.add_routes(manage_routes)

    web.run_app(app, port=8080)
