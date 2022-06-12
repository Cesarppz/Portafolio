from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from decouple import config

#CLAVE_DB = config('clave_postgres')
Session = None
engine = None
Base = declarative_base()

def init_base_db(url_base: str):
    """Instaciar la base de datos

    Args:
        url_base (str): Información con los datos para instanciar la base de datos

    Returns:
        tuple: Engine, Session, Base
    """
    
    global engine

    if engine == None:
        engine = create_engine(url_base)

        # Ver si la base de datos existe
        if not database_exists(engine.url):
            create_database(engine.url)

        global Session
        Session = sessionmaker(engine)

    return engine,Session,Base