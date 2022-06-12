import requests
import json
import logging
import traceback

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from decouple import config

#Request
RETRY_STRATEGY = Retry(total=5, backoff_factor=1,status_forcelist=[ 502, 503, 504 , 429])
session = requests.Session()
session.mount('https://',HTTPAdapter(max_retries=RETRY_STRATEGY))

# Authentication 
TOKEN = config('TOKEN')
USER_ZENDESK  = config('USER_ZENDESK')
AUTH = (USER_ZENDESK, TOKEN)

#Loger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API-Request')


def get_all_data(page:str, key:str) -> list : 
    """Hace un request a todas las páginas del endpoint en caso de tener más de una

    Args:
        page (str): Info del endpoint en json
        key (str): Nombre del endpoint

    Returns:
        list: La información de todas las páginas
    """
    try:
        if key == 'tickets':
            data = []
            data.extend(page['tickets'])

            while page['end_of_stream'] == False:
                page = get_info(link=page['after_url'])
                data.extend(page['tickets'])
            return data
        
        elif key == 'ticket_metrics' or key == 'views' or key == 'satisfaction_ratings':
            data = []
            data.extend(page[key])

            while page['meta']['has_more'] == True:
                page = get_info(link=page['links']['next'])
                data.extend(page[key])
            return data

        elif key == 'users':
            data = page['users']
            #data.extend(page['users'])

            while page['end_of_stream'] == False:
                page = get_info(link=page['next_page'])
                data.extend(page['users'])
            return data

        elif key == 'calls':
            data = page['calls']

            while page['count'] > 1:
                page = get_info(link=page['next_page'])
                data.extend(page['calls'])
            return data
            

        else:
            return page[key]
    
    except KeyError as ex_k:
        logger.error(f'Error al leer la información extraida (KeyError). En la categoria "{key}"')
        #traceback.print_exc(ex_k)
    except Exception as ex:
        logger.error(f'Error en el proceso de paginación. En la categoria "{key}"')
       # traceback.print_exc(ex)
                

def get_info(link: str,auth= AUTH) -> dict:
    """Hacer el primer request al endpoint

    Args:
        link (str): _description_
        auth (_type_, tuple): Autentificación en Zendesk. Defaults to AUTH.

    Raises:
        ValueError: Un request code diferente a 200
        ValueError: Request a un endpoint sin información

    Returns:
        dict: _description_
    """
    try:
        response = session.get(link, auth=auth)
        
        # Verificar el status code sea 200
        if response.status_code != 200:
            
            try:
                title_error =  response.json()['error']['title']
                message = response.json()['error']['message']
            
            except Exception:
                message = 'No hay mensaje'
                title_error = 'Error'

            raise ValueError(' Request con código {code}. {title}: {message})\n'.format(code=response.status_code,title=title_error , message=message))
        
        else:
            data = response.json()
            if data:
                return data
            else:
                raise ValueError('Diccionario vacío')
   
    except ValueError as err:
        logger.error('Error en el Request')
        print(err)


def request_to_api(link: str ,domain:str ,key: str, format=False, format_info= None ,format_id = None, ) -> dict: 
    """Hacer un todos los request al endpoint para extraer toda la información disponible

    Args:
        link (str): Url
        domain (str): Dominio del Zendesk
        key (str): Nombre del endpoint
        format (bool, optional): Verificación si el endpoint tiene pagination. Defaults to False.
        format_info (_type_, optional): Pagination. Defaults to None.
        format_id (_type_, optional): Nombre de del pagination del endpoint. Defaults to None.

    Returns:
        dict: Info extraida
    """

    # Format los links dependeindo de los requisitos de cada endpont
    if format:
        if format_id == 'time':
            link = link.format(time = format_info, domain = domain)

        elif format_id == 'id':
            link = link.format(id = format_info, domain = domain)

        elif format_id == 'agent_id':
            link = link.format(agent_id = format_info, domain = domain)

    else:
        link = link.format(domain = domain)

    page = get_info(link)
    #Si hay más páginas, hacer otro request
    page = get_all_data(page,key)

    return page
