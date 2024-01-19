import os
import uuid
from typing import List, Optional, Annotated
from uuid import UUID

import aiohttp as aiohttp
import aiopg
import fastapi
from fastapi import FastAPI, Header, APIRouter

from schema import Ticket, PagedResponse, TicketCreationSchema, TicketCreationResponse, TicketStatus

app = FastAPI(root_path='/api/v1', )

pool: aiopg.Pool

manage_router = APIRouter(prefix="/manage")


@manage_router.get('/health')
async def healthcheck():
    return fastapi.responses.Response()


app.include_router(manage_router)


async def query_flight(flight_number: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://0.0.0.0:8060/api/v1/flight/{flight_number}') as resp:
            return await resp.json()


@app.get('/tickets/{ticketUid}')
async def get_ticket_by_uid(ticketUid: UUID) -> Ticket:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT   id, '
                              '         ticket_uid, '
                              '         username, '
                              '         flight_number, '
                              '         price, '
                              '         status '
                              'FROM ticket '
                              'WHERE ticket_uid=%s '
                              'ORDER BY ticket.id ASC;', (ticketUid,))
            ticket_id, ticket_uid, username, flight_number, price, status = await cur.fetchone()
    return Ticket(ticket_id=ticket_id,
                  ticket_uid=ticket_uid,
                  username=username,
                  flight_number=flight_number,
                  price=price,
                  status=status, )


@app.delete('/tickets/{ticketUid}')
async def revoke_ticket_by_uid(ticketUid: UUID):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('UPDATE ticket '
                              'SET status=%s '
                              'WHERE ticket_uid=%s;', ('CANCELED', ticketUid,))
    return {}


@app.get('/tickets')
async def get_tickets(x_user_name: Annotated[str, Header()]) -> List[Ticket]:
    ret = []

    flight_raws = []
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT   id, '
                              '         ticket_uid, '
                              '         username, '
                              '         flight_number, '
                              '         price, '
                              '         status '
                              'FROM ticket '
                              'WHERE username=%s '
                              'ORDER BY ticket.id ASC;', (x_user_name,))
            async for ticket_id, ticket_uid, username, flight_number, price, status in cur:
                ret.append(
                    Ticket(ticket_id=ticket_id, ticket_uid=ticket_uid, username=username, flight_number=flight_number,
                           price=price, status=status, ))

    return ret


@app.post('/ticket')
async def post_ticket(body: TicketCreationSchema, x_user_name: Annotated[str, Header()]) -> TicketCreationResponse:
    ticket_uid = uuid.uuid4()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('INSERT INTO ticket '
                              '     (ticket_uid, username, flight_number, price, status) '
                              'VALUES '
                              '     (%s, %s, %s, %s, %s);',
                              (ticket_uid, x_user_name, body.flightNumber, body.price, 'PAID'))

    return TicketCreationResponse(ticketUid=ticket_uid,
                                  flightNumber=body.flightNumber,
                                  status=TicketStatus.PAID,
                                  price=body.price)


@app.on_event("startup")
async def startup_event():
    global pool
    dbname = os.environ.get('DB_NAME', 'ticket_service')
    user = os.environ.get('DB_USER', 'postgres')
    host = os.environ.get('DB_HOST', '0.0.0.0')
    password = os.environ.get('DB_PASSWORD', '0.0.0.0')
    dsn = f'dbname={dbname} user={user} password={password} host={host}'
    pool = await aiopg.create_pool(dsn)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
            CREATE TABLE IF NOT EXISTS ticket
(
    id            SERIAL PRIMARY KEY,
    ticket_uid    uuid UNIQUE NOT NULL,
    username      VARCHAR(80) NOT NULL,
    flight_number VARCHAR(20) NOT NULL,
    price         INT         NOT NULL,
    status        VARCHAR(20) NOT NULL
        CHECK (status IN ('PAID', 'CANCELED'))
);
            ''')
