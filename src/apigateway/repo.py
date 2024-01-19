from typing import List

import schema
from db_conn import db_conn
from schema import PersonResponse, ErrorResponse, PersonRequest, ErrorNotFound


class PersonaRepo:
    @staticmethod
    def find_by_id(_id: int) -> PersonResponse:
        with db_conn() as db:
            with db.cursor() as cur:
                cur.execute('SELECT id, name, age, addr, work_name '
                            'FROM persons '
                            'WHERE id=%s;', (_id,))
                dat = cur.fetchone()
        if dat is None:
            raise ErrorResponse(f'Person not found with id {_id}')
        return PersonResponse(*dat)

    @staticmethod
    def find() -> List[PersonResponse]:
        with db_conn() as db:
            with db.cursor() as cur:
                cur.execute('SELECT id, name, age, addr, work_name '
                            'FROM persons '
                            'ORDER BY id DESC;')

                res = list(map(lambda x: PersonResponse(*x), cur))
        return res

    @staticmethod
    def delete(_id: int):
        with db_conn() as db:
            with db.cursor() as cur:
                cur.execute('SELECT 1 FROM persons WHERE id=%s;', (_id,))

                if cur.fetchone() is None:
                    raise ErrorNotFound()

                cur.execute('DELETE FROM persons '
                            'WHERE  id=%s;', (_id,))
            db.commit()

    @staticmethod
    def create(req: PersonRequest) -> PersonResponse:
        with db_conn() as db:
            with db.cursor() as cur:
                cur.execute('INSERT INTO persons '
                            '   (name, work_name, addr, age) '
                            'VALUES '
                            '   (%s, %s, %s, %s) '
                            'RETURNING id;', (req.name, req.work, req.address, req.age))
                _id, = cur.fetchone()
            db.commit()
        return PersonResponse.from_request(_id, req)

    @staticmethod
    def patch(_id: int, req_dat: dict) -> PersonResponse:
        with db_conn() as db:
            with db.cursor() as cur:
                cur.execute('SELECT 1 FROM persons WHERE id=%s;', (_id,))
                if cur.fetchone() is None:
                    raise ErrorNotFound()
                for k, v in req_dat.items():
                    if k == 'address':
                        k = 'addr'
                    if k == 'work':
                        k = 'work_name'
                    cur.execute('UPDATE persons '
                                f'SET    {k}=%s '
                                'WHERE  id=%s;',
                                (v, _id))
            db.commit()
        return PersonaRepo.find_by_id(_id)
