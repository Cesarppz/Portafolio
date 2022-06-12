#!/usr/bin/env python
import datetime
import logging
import argparse

from datetime import timezone
from read_yaml import read_yaml
from request import request_to_api
from insert import load_to_db
from queries import get_last_request
from base import init_base_db

from decouple import config

#logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API')

# Agent ID
__AGENT_ID = config('AGENT_ID')


TODAY = datetime.datetime.now()
TODAY = TODAY - datetime.timedelta(days=365,minutes=1)   # Se le resta un minuto por buenas practicas de la API  # Por ahora uso data del año pasado para poder hacer los test
TODAY = TODAY.replace(second=0, microsecond=0)
TODAY_TIMESTAMP = int(TODAY.replace(tzinfo=timezone.utc).timestamp()) 


def request_all_categories(domain:str, categories:dict, request_date) -> dict:
    """Por cada URL en el archivo links.yaml, hago un llamo a la función request_to_api, para hacer un request al endpoint

    Args:
        domain (str): Dominio del zendesk
        categories (dict): Diferentes categorías de la api Zendesk
        request_date (int): Última fecha en la que se hizo un request

    Returns:
        dict: Info de todos los endponts
    """
    category_name = []
    category_data = []

    for category in categories.values():
        for key, value in category.items():

            if value['format'][0] == True:
                
                if value['format'][-1] == 'time':

                    data = request_to_api(value['link'],domain,format=value['format'][0],format_id=value['format'][-1], format_info=request_date, key=key)
            
            else:
                data = request_to_api(value['link'] ,domain , key=key)

            logger.info(f'Información extraida Endpoint:{key}')
            category_name.append(key)
            category_data.append(data)

    return {
        'Category_names':category_name,
        'Category_data':category_data
        }


def main(args) -> None:
    """Función raiz, que ejecuta todas los modulos del progrma

    Args:
        args (Class): Argumentos instanciados (Domain, Base)
    """

    categories = read_yaml()
    logger.info('Información leida')
    engine,Session,Base = init_base_db(args.Base)
    request_date = get_last_request(Session)
    data = request_all_categories(args.Domain,categories, request_date)
    load_to_db(engine,Session,Base,data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('--Domain','-d', type=str, help='Domain al que se va a conectar con Zendesk')
    parser.add_argument('--Base','-b', type=str,help='Agrege el nombre de la base de datos que desea utilizar o crear')
    args = parser.parse_args()


    if args.Domain == None or args.Base == None:
        logger.error('Los argumentos no pueden ser nulos')

    else: 
        args.Base = '{base_url}/{db}'.format(base_url=config('BASE_URL'), db=args.Base)
        main(args)