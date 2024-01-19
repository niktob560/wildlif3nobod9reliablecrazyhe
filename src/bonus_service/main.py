import os
from datetime import timezone
from typing import Annotated
from uuid import UUID

import aiopg
import fastapi.exceptions
from fastapi import FastAPI, Header, APIRouter

from schema import PrivilegeResponse, PrivilegeHistoryItemResponse, PushPrivilegeRequest, PrivilegeHistoryOperationType

app = FastAPI(root_path='/api/v1', )

pool: aiopg.Pool

manage_router = APIRouter(prefix="/manage")


@manage_router.get('/health')
async def healthcheck():
    return fastapi.responses.Response()


app.include_router(manage_router)


@app.get('/privilege')
async def get_user_privilege(x_user_name: Annotated[str, Header()]) -> PrivilegeResponse:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT   id, status, balance '
                              'FROM privilege '
                              'WHERE username=%s;', (x_user_name,))
            dat = await cur.fetchone()

            if dat is None:
                await cur.execute('INSERT INTO privilege '
                                  '     (username, balance) '
                                  'VALUES '
                                  '     (%s, 0) '
                                  'RETURNING id, status, balance;',
                                  (x_user_name,))
                dat = await cur.fetchone()

            privilege_id, status, balance = dat
            if balance is None:
                balance = 0
            history = []
            await cur.execute('SELECT   ticket_uid, '
                              '         datetime, '
                              '         balance_diff, '
                              '         operation_type '
                              'FROM privilege_history '
                              'WHERE privilege_id=%s;', (privilege_id,))
            async for ticket_uid, dt, balance_diff, op_type in cur:
                history.append(PrivilegeHistoryItemResponse(
                    date=dt.replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    ticketUid=ticket_uid,
                    balanceDiff=balance_diff,
                    operationType=op_type
                ))
            return PrivilegeResponse(balance=balance, status=status, history=history)


@app.post('/privilege')
async def push_privilege(body: PushPrivilegeRequest, x_user_name: Annotated[str, Header()]):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT   id, status, balance '
                              'FROM privilege '
                              'WHERE username=%s;', (x_user_name,))
            privilege_id, status, balance = await cur.fetchone()
            balance_diff = body.price
            if body.operationType == PrivilegeHistoryOperationType.FILL_IN_BALANCE:
                balance_diff = int(balance_diff * 0.1)
            else:
                balance_diff = -1 * min(balance, balance_diff)
            await cur.execute('INSERT INTO privilege_history '
                              '     (privilege_id, ticket_uid, datetime, balance_diff, operation_type) '
                              'VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s);',
                              (privilege_id, body.ticket_uid, balance_diff, str(body.operationType.name)))

            await cur.execute('UPDATE privilege '
                              'SET balance=balance+%s '
                              'WHERE id=%s;', (balance_diff, privilege_id))


@app.delete('/privilege/{ticketUid}')
async def drop_privilege(ticketUid: UUID):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('SELECT   id, privilege_id, balance_diff, operation_type '
                              'FROM privilege_history '
                              'WHERE ticket_uid=%s;', (ticketUid,))
            dat = await cur.fetchone()
            if dat is None:
                raise fastapi.exceptions.HTTPException(404)

            history_id, privilege_id, balance_diff, op_type = dat
            await cur.execute('SELECT   id, status, balance '
                              'FROM privilege '
                              'WHERE id=%s;', (privilege_id,))

            privilege_id, status, balance = await cur.fetchone()
            await cur.execute('DELETE FROM privilege_history '
                              'WHERE ticket_uid=%s;', (ticketUid,))

            await cur.execute('UPDATE privilege '
                              'SET balance=balance-%s '
                              'WHERE id=%s;', (min(balance, balance_diff), privilege_id))


@app.on_event("startup")
async def startup_event():
    global pool
    dbname = os.environ.get('DB_NAME', 'bonus_service')
    user = os.environ.get('DB_USER', 'postgres')
    host = os.environ.get('DB_HOST', '0.0.0.0')
    password = os.environ.get('DB_PASSWORD', '0.0.0.0')
    dsn = f'dbname={dbname} user={user} password={password} host={host}'
    pool = await aiopg.create_pool(dsn)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
            CREATE TABLE IF NOT EXISTS privilege
(
    id       SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    status   VARCHAR(80) NOT NULL DEFAULT 'BRONZE'
        CHECK (status IN ('BRONZE', 'SILVER', 'GOLD')),
    balance  INT
);
            ''')
            await cur.execute('''
            CREATE TABLE IF NOT EXISTS privilege_history
(
    id             SERIAL PRIMARY KEY,
    privilege_id   INT REFERENCES privilege (id),
    ticket_uid     uuid        NOT NULL,
    datetime       TIMESTAMP   NOT NULL,
    balance_diff   INT         NOT NULL,
    operation_type VARCHAR(20) NOT NULL
        CHECK (operation_type IN ('FILL_IN_BALANCE', 'DEBIT_THE_ACCOUNT'))
);
''')
