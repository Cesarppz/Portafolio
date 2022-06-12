import datetime
import sqlalchemy
from datetime import timezone

from tables.records import Record

# Date 
NOW = datetime.datetime.now()


def __convert_datetime(last_request_date):
    """Hace la resta de los días que han pasado desde la última ejecució y me lo devuelve en el formato adecuado para hacer el request a la api

    Args:
        last_request_date (DateTime): La última vez que se ejecutó el programa

    Returns:
        int: La fecha para hacer el request
    """
    date = NOW - last_request_date
    request_date = NOW - date
    request_date = request_date.replace(second=0, microsecond=0)
    request_date = int(request_date.replace(tzinfo=timezone.utc).timestamp())
    
    return request_date


def get_last_request(Session):
    """Crea una session en la base de datos, y hace un query en la tabla Records, para buscar la última fecha en la que se ejecutó el programa.
    En caso de que no haya un fecha predesesora, se tomará como fecha un año antrás.

    Args:
        Session (Class): Session en el manejador de base de datos

    Returns:
        int: fecha en la que hizo el último request
    """
    session = Session()
    
    try:
        query = session.query(Record).order_by(Record.id.desc()).first()
        last_request_date = query.created_at
        request_date = __convert_datetime(last_request_date)
        
        return request_date 
    
    except sqlalchemy.exc.ProgrammingError as at:
        date = datetime.datetime.now()
        date = date - datetime.timedelta(days=365,minutes=1)   # Se le resta un minuto por buenas practicas de la API  # Por ahora uso data del año pasado para poder hacer los test
        date = date.replace(second=0, microsecond=0)
        date_timestamp = int(date.replace(tzinfo=timezone.utc).timestamp()) 

        return date_timestamp

    

    


