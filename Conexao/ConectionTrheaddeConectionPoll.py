import psycopg2 
from dotenv import load_dotenv
import os
from psycopg2.pool import ThreadedConnectionPool

load_dotenv()

  
  
class DbConfig:
    HOST = os.getenv("DB_HOST")
    PORT = port = os.getenv("DB_PORT")
    DATABASE = os.getenv("DB_DATA_BASE")
    USER = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASSWORD")



class DbConnect:
    def __init__(self, config: DbConfig, auto_commit: bool = True):
        self.config = config
        self.connection = None
        self.auto_commit = auto_commit
        
    def __enter__(self):
        self.connection = psycopg2.connect(
            host=self.config.HOST,
            port=self.config.PORT,
            database=self.config.DATABASE,
            user=self.config.USER,
            password=self.config.PASSWORD
        )
        return self.connection
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            if exc_type is None and self.auto_commit:
                self.connection.commit()
            elif exc_type is not None:
                self.connection.rollback()
            self.connection.close()

    @classmethod
    def get_pool(cls, maxconn=10):
        if cls._pool is None:
            cls._pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=maxconn,
                **cls.DbConfig()
            )
        return cls._pool
