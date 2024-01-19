import os
from typing import Optional

import psycopg2
import psycopg2.extensions

import psycopg2.pool

db_pool: Optional[psycopg2.pool.SimpleConnectionPool] = None


class db_conn:
    def __enter__(self) -> psycopg2.extensions.connection:
        global db_pool
        if db_pool is None:
            db_username = os.environ.get('PSQL_USER', 'postgres')
            db_password = os.environ.get('PSQL_PASSWORD', 'pass')
            db_hostname = os.environ.get('PSQL_HOST', '127.0.0.1')
            db_name = os.environ.get('PSQL_NAME', 'postgres')
            db_port = os.environ.get('PSQL_PORT', 15432)
            db_pool = psycopg2.pool.SimpleConnectionPool(maxconn=16,
                                                         minconn=2,
                                                         database=db_name,
                                                         user=db_username,
                                                         password=db_password,
                                                         host=db_hostname,
                                                         port=db_port)

        self._con = db_pool.getconn()
        return self._con

    def __exit__(self, exc_type, exc_val, exc_tb):
        db_pool.putconn(self._con)
