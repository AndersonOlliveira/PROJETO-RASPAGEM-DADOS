from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from Conexao.ConectionClass import DbConfig  # ajuste o import conforme seu projeto

class DbPool:
    def __init__(self,config, maxconn=10):
    # def __init__(self, maxconn=10):
        print(f"config enviado {config}")
        self.config = config
        self.pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=maxconn,
            # host=DbConfig.HOST,
            # port=DbConfig.PORT,
            # database=DbConfig.DATABASE,
            # user=DbConfig.USER,
            # password=DbConfig.PASSWORD
            host= self.config.HOST,
            port= self.config.PORT,
            database= self.config.DATABASE,
            user= self.config.USER,
            password= self.config.PASSWORD
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