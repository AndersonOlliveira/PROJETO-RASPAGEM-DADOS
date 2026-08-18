from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from Conexao.ConectionClass import DbConfig  # ajuste o import conforme seu projeto

class DbPool:
    def __init__(self, maxconn=10):
        self.pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=maxconn,
            host=DbConfig.HOST,
            port=DbConfig.PORT,
            database=DbConfig.DATABASE,
            user=DbConfig.USER,
            password=DbConfig.PASSWORD
        )

    @contextmanager
    def get_connection(self):
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)