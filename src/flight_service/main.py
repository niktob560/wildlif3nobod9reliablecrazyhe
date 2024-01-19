import datetime
import os
from collections import namedtuple
from typing import Optional, List

import aiopg
import fastapi
from fastapi import FastAPI, APIRouter

from schema import Airport, Flight, PagedResponse

app = FastAPI(root_path='/api/v1', )

pool: aiopg.Pool

manage_router = APIRouter(prefix="/manage")


@manage_router.get('/health')
async def healthcheck():
    return fastapi.responses.Response()


app.include_router(manage_router)


@app.get('/airport/{airport_id}')
async def get_airport_by_id(airport_id: int) -> Airport:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT   id, '
                              '         name, '
                              '         city, '
                              '         country '
                              'FROM airport '
                              'WHERE id=%s;', (airport_id,))
            dat = await cur.fetchone()
            if dat is None:
                raise fastapi.exceptions.HTTPException(404)
            airport_id, name, city, country = dat
            return Airport(id=airport_id, name=name, city=city, country=country, )


@app.get('/flight/{flightNumber}')
async def get_flight_by_number(flightNumber: str) -> Flight:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT   flight.id, '
                              '         flight.flight_number, '
                              '         flight.datetime, '
                              '         flight.from_airport_id, '
                              '         flight.to_airport_id, '
                              '         flight.price '
                              'FROM flight '
                              'WHERE flight_number=%s '
                              'ORDER BY flight.datetime DESC '
                              'LIMIT 1;', (flightNumber,))
            dat = await cur.fetchone()
            if dat is None:
                raise fastapi.exceptions.HTTPException(404)
            flight_id, flight_number, flight_datetime, flight_from_airport_id, flight_to_airport_id, flight_price = dat
    from_airport = await get_airport_by_id(flight_from_airport_id)
    to_airport = await get_airport_by_id(flight_to_airport_id)

    return Flight(id=flight_id,
                  flightNumber=flight_number,
                  date=flight_datetime.strftime('%Y-%m-%d %H:%M'),
                  fromAirport=from_airport.city + ' ' + from_airport.name,
                  toAirport=to_airport.city + ' ' + to_airport.name,
                  price=flight_price)


@app.get('/flights')
async def get_all_flights(page: Optional[int] = None,
                          size: Optional[int] = None) -> PagedResponse[Flight]:
    size = size or 100
    page = page or 0
    offset = page * size
    ret = []

    FlightRaw = namedtuple('FlightRaw', ['flight_id', 'flight_number', 'dt', 'from_id', 'to_id', 'price'])

    flight_raws = []
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT   flight.id, '
                              '         flight.flight_number, '
                              '         flight.datetime, '
                              '         flight.from_airport_id, '
                              '         flight.to_airport_id, '
                              '         flight.price '
                              'FROM flight '
                              'ORDER BY flight.id ASC '
                              'OFFSET %s '
                              'LIMIT %s;', (offset, size,))
            async for row in cur:
                flight_raws.append(FlightRaw(*row))

    for flight_raw in flight_raws:
        from_airport = await get_airport_by_id(flight_raw.from_id)
        to_airport = await get_airport_by_id(flight_raw.to_id)
        ret.append(Flight(id=flight_raw.flight_id,
                          flightNumber=flight_raw.flight_number,
                          date=flight_raw.dt.strftime('%Y-%m-%d %H:%M'),
                          fromAirport=from_airport.city + ' ' + from_airport.name,
                          toAirport=to_airport.city + ' ' + to_airport.name,
                          price=flight_raw.price))

    return PagedResponse(page=page, pageSize=size, totalElements=len(ret), items=ret)


@app.get('/airports')
async def get_all_airports(page: Optional[int] = None, size: Optional[int] = None) -> List[Airport]:
    size = size or 100
    offset = (page or 0) * size
    ret = []

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT   id, '
                              '         name, '
                              '         city, '
                              '         country '
                              'FROM airport '
                              'ORDER BY id ASC '
                              'OFFSET %s '
                              'LIMIT %s;', (offset, size,))
            async for airport_id, name, city, country in cur:
                ret.append(Airport(id=airport_id, name=name, city=city, country=country, ))
    return ret


@app.on_event("startup")
async def startup_event():
    global pool
    dbname = os.environ.get('DB_NAME', 'flight_service')
    user = os.environ.get('DB_USER', 'postgres')
    host = os.environ.get('DB_HOST', '0.0.0.0')
    password = os.environ.get('DB_PASSWORD', '0.0.0.0')
    dsn = f'dbname={dbname} user={user} password={password} host={host}'
    pool = await aiopg.create_pool(dsn)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
            CREATE TABLE IF NOT EXISTS airport
(
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(255),
    city    VARCHAR(255),
    country VARCHAR(255)
);''')
            await cur.execute('''
            CREATE TABLE IF NOT EXISTS flight
(
    id              SERIAL PRIMARY KEY,
    flight_number   VARCHAR(20)              NOT NULL,
    datetime        TIMESTAMP WITH TIME ZONE NOT NULL,
    from_airport_id INT REFERENCES airport (id),
    to_airport_id   INT REFERENCES airport (id),
    price           INT                      NOT NULL
);
            ''')

            await cur.execute('INSERT INTO airport '
                              ' (name, city, country) '
                              'VALUES '
                              ' (%s, %s, %s)', ('Шереметьево', 'Москва', 'Россия'))

            await cur.execute('INSERT INTO airport '
                              ' (name, city, country) '
                              'VALUES '
                              ' (%s, %s, %s)', ('Пулково', 'Санкт-Петербург', 'Россия'))

            await cur.execute('INSERT INTO flight '
                              '   (flight_number, datetime, from_airport_id, to_airport_id, price) '
                              'VALUES '
                              '   (%s, %s, %s, %s, %s);', ('AFL031', '2021-10-08 20:00', 2, 1, 1500))
