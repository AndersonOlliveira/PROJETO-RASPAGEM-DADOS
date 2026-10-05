from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from Conexao.ConectionClass import DbConfig  # ajuste o import conforme seu projeto
from threading import BoundedSemaphore


class DbPool:

    def __init__(self, config, maxconn=3):

        print("==========================================")
        print("CRIANDO CONNECTION POOL")
        print("MAX CONNECTIONS:", maxconn)
        print("==========================================")

        self.config = config
        self.maxconn = maxconn

        # ============================================================
        # POOL DO POSTGRES
        # ============================================================

        self.pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=maxconn,
            host=self.config.HOST,
            port=self.config.PORT,
            database=self.config.DATABASE,
            user=self.config.USER,
            password=self.config.PASSWORD
        )

        # ============================================================
        # CONTROLE DE CONCORRÊNCIA
        #
        # O psycopg2 não espera quando o pool está cheio.
        #
        # O Semaphore faz a thread esperar até existir
        # uma conexão disponível.
        # ============================================================

        self.semaphore = BoundedSemaphore(maxconn)

    @contextmanager
    def get_connection(self):

        conn = None

        # ============================================================
        # ESPERA UMA VAGA NO POOL
        # ============================================================

        self.semaphore.acquire()

        try:

            print(
                "[POOL] AGUARDANDO/ENTRANDO | "
                "used:",
                len(self.pool._used),
                "| free:",
                len(self.pool._pool),
                "| max:",
                self.maxconn
            )

            # ========================================================
            # PEGA A CONEXÃO
            # ========================================================

            conn = self.pool.getconn()

            print(
                "[POOL] CONEXÃO OBTIDA | "
                "used:",
                len(self.pool._used),
                "| free:",
                len(self.pool._pool),
                "| max:",
                self.maxconn
            )

            # ========================================================
            # ENTREGA A CONEXÃO PARA O CÓDIGO
            # ========================================================

            yield conn

            # ========================================================
            # COMMIT
            # ========================================================

            conn.commit()

        except Exception:

            # ========================================================
            # ROLLBACK
            # ========================================================

            if conn is not None:

                try:
                    conn.rollback()
                except Exception:
                    pass

            raise

        finally:

            # ========================================================
            # DEVOLVE A CONEXÃO AO POOL
            # ========================================================

            if conn is not None:

                try:

                    self.pool.putconn(conn)

                    print(
                        "[POOL] CONEXÃO DEVOLVIDA | "
                        "used:",
                        len(self.pool._used),
                        "| free:",
                        len(self.pool._pool),
                        "| max:",
                        self.maxconn
                    )

                except Exception as e:

                    print(
                        "[POOL] ERRO AO DEVOLVER CONEXÃO:",
                        repr(e)
                    )

            # ========================================================
            # LIBERA A VAGA PARA OUTRA THREAD
            # ========================================================

            self.semaphore.release()

    def close_all(self):

        try:
            self.pool.closeall()
        except Exception:
            pass