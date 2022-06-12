import logging
import datetime

from sqlalchemy import exists, and_

from tables.ticket import Ticket, Custom_field, Field, Ticket_Metrics, User
from tables.views  import View 
from tables.ticket_metrics import Ticket_Metrics
from tables.users import User
from tables.satisfaction_ratings import SatisfactionRating
from tables.schedules import Schedule, Interval
from tables.stats import Stats
from tables.records import Record
from tables.calls import Call

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API')


def insert_no_duplicates(row, session, object):
    """Verficar si los datos entán repetidos en la base de datos

    Args:
        row             : Row en la base de datos
        session (class) :  Session (Manejador de base de datos)
        object (object) : Tabla en la base de datos
    """

    try:  
        if object == Stats:
            if not session.query(exists().where(object.updated_at <= row.updated_at)).scalar():
                session.add(row)

        elif object == Record:
            if not session.query(exists().where(object.created_at == row.created_at)).scalar():
                session.add(row)

        else:
            if not session.query(exists().where(and_( object.id==row.id,  and_(object.id==row.id,object.updated_at <= row.updated_at) ))).scalar():
                session.add(row)

    except Exception as ex:
        logger.error('Error al filtrar los datos. Error:', ex)


def insert_registers(data, idx, info_dict,session)-> None:
    """Por cada tabla y subtabla, insertar los datos que no estén repetidos

    Args:
        data (dict): Nombre de los endponts
        idx (_type_): puntero
        info_dict (_type_): Data a insertar
        session (_type_):  Session (Manejador de base de datos)
    """
    for info in info_dict:
        if data['Category_names'][idx] == 'tickets':     
            #Ticket
            insert_no_duplicates(Ticket(**info), session, Ticket)
            
            # Custom fields
            for row in info['custom_fields']:
                row['ticket_id']  = info['id']
                row['updated_at'] = info['updated_at']
                row['created_at'] = info['created_at']
                insert_no_duplicates(Custom_field(**row), session, Custom_field)
            
            # Fields
            for row in info['fields']:
                row['ticket_id']  = info['id']
                row['updated_at'] = info['updated_at']
                row['created_at'] = info['created_at']
                insert_no_duplicates(Field(**row), session, Field)

        elif data['Category_names'][idx] == 'ticket_metrics':
            try:
                insert_no_duplicates(Ticket_Metrics(**info), session, Ticket_Metrics)
                
            except Exception as ext:
                logger.error('Error generado al instanciar la tabla ticket_metrics')

        elif data['Category_names'][idx] == 'users':
            insert_no_duplicates(User(**info), session, User)

        elif data['Category_names'][idx] == 'views':
            insert_no_duplicates(View(**info), session, View)

        elif data['Category_names'][idx] == 'schedules':
            insert_no_duplicates(Schedule(**info), session, Schedule)
            #Intervals
            for row in info['intervals']:
                row['id']   = info['id']
                row['updated_at'] = info['updated_at']
                row['created_at'] = info['created_at']
                insert_no_duplicates(Interval(**row), session, Interval)

        elif data['Category_names'][idx] == 'satisfaction_ratings':
            insert_no_duplicates(SatisfactionRating(**info), session, SatisfactionRating)

        elif data['Category_names'][idx] == 'account_overview':
            insert_no_duplicates(Stats(**info), session, Stats)

        elif data['Category_names'][idx] == 'calls':
            insert_no_duplicates(Call(**info), session, Call)
        

def load_tables(data:dict , session) -> None:
    """Insertar los datos pertinentes en las tablas

    Args:
        data (dict): Datos a insertar
        session (_type_): Session (Manejador de base de datos)
    """
    try:
        
        if len(data['Category_data']) >= 1:
            for idx, info_dict in enumerate(data['Category_data']):
                
                if type(info_dict) != list:
                    info_dict = [info_dict]
                
                if len(info_dict) >= 1:
                    insert_registers(data, idx, info_dict, session)

            insert_no_duplicates(Record(created_at=datetime.datetime.now().replace(second=0, microsecond=0)), session, Record)        
            session.commit()    
            session.close()

    except Exception as ex:
        logger.error('Error generado al instanciar los datos a la en la tabla . Error: \n{}'.format(ex))


def load_to_db(engine, Session, Base, data) -> None:
    """Insertar los datos extraidos en la base de datos

    Args:
        engine (class): engine (Manejador de base de datos)
        Session (class): session (Manejador de base de datos)
        Base (class): Base (Manejador de base de datos)
        data (dict): Data a insertar
    """
    session = Session()
    Base.metadata.create_all(engine)
    
    
    try:
        load_tables(data, session)        
        logger.info('>>> Datos añadidos sastifactoriamente a la base de datos')
    
    except Exception as err:
        logger.error('Error detectado {}'.format(err))
  
