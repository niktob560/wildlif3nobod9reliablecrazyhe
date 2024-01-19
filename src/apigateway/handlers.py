import os
from typing import List
from uuid import UUID

import aiohttp
from aiohttp import web

from repo import PersonaRepo
from route import routes
from schema import PersonRequest
from schema import PersonResponse


async def get_flight_by_number(flight_number: str) -> dict:
    flight_baseurl = os.environ.get('FLIGHT_BASEURL', 'http://0.0.0.0:8060/api/v1')
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{flight_baseurl}/flight/{flight_number}') as resp:
            return await resp.json()


@routes.get('/flights')
async def get_flights(request: web.Request):
    page = int(request.rel_url.query.get('page'))
    size = int(request.rel_url.query.get('size'))
    flight_baseurl = os.environ.get('FLIGHT_BASEURL', 'http://0.0.0.0:8060/api/v1')
    async with aiohttp.ClientSession() as session:
        u = f'{flight_baseurl}/flights'
        if page is not None or size is not None:
            u += '?'
        if page is not None:
            u += f'page={page - 1}'
            if size is not None:
                u += '&'
        if size is not None:
            u += f'size={size}'

        async with session.get(u) as resp:
            flights = await resp.json()

    dat = flights.copy()
    dat['items'] = []
    for f in flights['items']:
        dat['items'].append({
            "flightNumber": f['flightNumber'],
            "fromAirport": f['fromAirport'],
            "toAirport": f['toAirport'],
            "date": f['date'],
            "price": f['price'],
        })

    return aiohttp.web.json_response(dat)


@routes.get('/tickets')
async def get_tickets(request: web.Request):
    user_name = request.headers.get('X-User-Name')
    headers = {}
    if user_name is not None:
        headers['X-User-Name'] = user_name
    else:
        return aiohttp.web.Response(status=400)
    ticket_baseurl = os.environ.get('TICKET_BASEURL', 'http://0.0.0.0:8070/api/v1')
    async with aiohttp.ClientSession(headers=headers) as session:
        u = f'{ticket_baseurl}/tickets'
        async with session.get(u) as resp:
            tickets: dict = await resp.json()

    dat = []
    for t in tickets:
        flight_number = t['flight_number']
        flight_data = await get_flight_by_number(flight_number)
        dat.append({
            "ticketUid": t['ticket_uid'],
            "status": t['status'],
            'flightNumber': flight_number,
            'fromAirport': flight_data['fromAirport'],
            'toAirport': flight_data['toAirport'],
            'date': flight_data['date'],
            'price': t['price']
        })

    return aiohttp.web.json_response(dat)


@routes.get('/privilege')
async def get_privilege(request: web.Request):
    user_name = request.headers.get('X-User-Name')
    headers = {}
    if user_name is not None:
        headers['X-User-Name'] = user_name
    else:
        return aiohttp.web.Response(status=400)
    bonus_baseurl = os.environ.get('BONUS_BASEURL', 'http://0.0.0.0:8080/api/v1')
    async with aiohttp.ClientSession(headers={'X-User-Name': user_name}) as session:
        async with session.get(f'{bonus_baseurl}/privilege') as resp:
            return web.json_response(await resp.json())


@routes.get('/me')
async def get_me(request: web.Request):
    user_name = request.headers['X-User-Name']

    headers = {}
    if user_name is not None:
        headers['X-User-Name'] = user_name
    ticket_baseurl = os.environ.get('TICKET_BASEURL', 'http://0.0.0.0:8070/api/v1')
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f'{ticket_baseurl}/tickets') as resp:
            tickets = await resp.json()

    bonus_baseurl = os.environ.get('BONUS_BASEURL', 'http://0.0.0.0:8080/api/v1')
    async with aiohttp.ClientSession(headers={'X-User-Name': user_name}) as session:
        async with session.get(f'{bonus_baseurl}/privilege') as resp:
            privilege_data = await resp.json()

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f'{ticket_baseurl}/tickets') as resp:
            tickets = await resp.json()
    dat = []
    for t in tickets:
        flight_data = await get_flight_by_number(t['flight_number'])
        dat.append({
            "ticketUid": t['ticket_uid'],
            "flightNumber": t['flight_number'],
            'fromAirport': flight_data['fromAirport'],
            'toAirport': flight_data['toAirport'],
            'date': flight_data['date'],
            "price": t['price'],
            "status": t['status']
        })
    return aiohttp.web.json_response({
        'tickets': dat,
        'privilege': {
            "balance": privilege_data['balance'],
            "status": privilege_data['status']
        }
    })


@routes.post('/tickets')
async def post_ticket(request: web.Request):
    if 'X-User-Name' not in request.headers.keys():
        return aiohttp.web.Response(status=400)
    user_name = request.headers['X-User-Name']
    dat = await request.json()
    if 'flightNumber' not in dat.keys():
        return aiohttp.web.Response(status=400)
    if 'price' not in dat.keys():
        return aiohttp.web.Response(status=400)
    if 'paidFromBalance' not in dat.keys():
        return aiohttp.web.Response(status=400)
    flight_number = dat['flightNumber']
    price = dat['price']
    paid_from_balance = dat['paidFromBalance']

    flight_baseurl = os.environ.get('FLIGHT_BASEURL', 'http://0.0.0.0:8060/api/v1')
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{flight_baseurl}/flight/{flight_number}') as resp:
            if resp.status != 200:
                return aiohttp.web.Response(status=resp.status)
            flight_info = await resp.json()

    ticket_baseurl = os.environ.get('TICKET_BASEURL', 'http://0.0.0.0:8070/api/v1')
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{ticket_baseurl}/ticket', json=dat, headers={'X-User-Name': user_name}) as resp:
            ticket = await resp.json()
    ticket_uid = ticket['ticketUid']

    bonus_baseurl = os.environ.get('BONUS_BASEURL', 'http://0.0.0.0:8080/api/v1')
    async with aiohttp.ClientSession(headers={'X-User-Name': user_name}) as session:
        async with session.get(f'{bonus_baseurl}/privilege') as resp:
            privilege_data = await resp.json()

    priv_balance = privilege_data['balance']

    paid_bonuses = 0
    paid_money = price
    operation = 'FILL_IN_BALANCE'
    operation_price = price

    if paid_from_balance:
        paid_bonuses = min(priv_balance, price)
        paid_money -= paid_bonuses
        operation = 'DEBIT_THE_ACCOUNT'
        operation_price = paid_bonuses

    async with aiohttp.ClientSession(headers={'X-User-Name': user_name}) as session:
        async with session.post(f'{bonus_baseurl}/privilege', json={
            'operationType': operation,
            'price': operation_price,
            'ticket_uid': str(ticket_uid)
        }) as resp:
            pass

    bonus_baseurl = os.environ.get('BONUS_BASEURL', 'http://0.0.0.0:8080/api/v1')
    async with aiohttp.ClientSession(headers={'X-User-Name': user_name}) as session:
        async with session.get(f'{bonus_baseurl}/privilege') as resp:
            privilege_data = await resp.json()

    return aiohttp.web.json_response({
        "ticketUid": ticket_uid,
        "flightNumber": flight_info['flightNumber'],
        "fromAirport": flight_info['fromAirport'],
        "toAirport": flight_info['toAirport'],
        "date": flight_info['date'],
        "price": price,
        "paidByMoney": paid_money,
        "paidByBonuses": paid_bonuses,
        "status": "PAID",
        "privilege": {
            "balance": privilege_data['balance'],
            "status": privilege_data['status']
        }
    })


@routes.get('/tickets/{ticketUid}')
async def get_ticket(request: web.Request):
    r = request.match_info
    if 'ticketUid' not in r.keys():
        return aiohttp.web.Response(status=400)
    ticket_uid = r['ticketUid']

    if 'X-User-Name' not in request.headers.keys():
        return aiohttp.web.Response(status=400)
    user_name = request.headers['X-User-Name']

    ticket_baseurl = os.environ.get('TICKET_BASEURL', 'http://0.0.0.0:8070/api/v1')
    async with aiohttp.ClientSession(headers={'X-User-Name': user_name}) as session:
        async with session.get(f'{ticket_baseurl}/tickets/{ticket_uid}') as resp:
            dat = await resp.json()

    flight_data = await get_flight_by_number(dat['flight_number'])
    return aiohttp.web.json_response({
        "ticketUid": dat['ticket_uid'],
        "flightNumber": dat['flight_number'],
        'fromAirport': flight_data['fromAirport'],
        'toAirport': flight_data['toAirport'],
        'date': flight_data['date'],
        "price": dat['price'],
        "status": dat['status']
    })


@routes.delete('/tickets/{ticketUid}')
async def revoke_ticket(request: web.Request):
    r = request.match_info
    if 'ticketUid' not in r.keys():
        return aiohttp.web.Response(status=400)
    ticket_uid = r['ticketUid']

    bonus_baseurl = os.environ.get('BONUS_BASEURL', 'http://0.0.0.0:8080/api/v1')
    async with aiohttp.ClientSession() as session:
        async with session.delete(f'{bonus_baseurl}/privilege/{ticket_uid}') as resp:
            if resp.status >= 400:
                return web.Response(status=204)
            _ = await resp.json()

    ticket_baseurl = os.environ.get('TICKET_BASEURL', 'http://0.0.0.0:8070/api/v1')
    async with aiohttp.ClientSession() as session:
        async with session.delete(f'{ticket_baseurl}/ticket/{ticket_uid}') as resp:
            _ = await resp.json()

    return web.Response(status=204)
