import yaml 
import logging

#Loger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Zendesk-API')

__config = None


def read_yaml(path='./links.yaml') -> dict:
    """Lee el archivo link.yaml donde está la información de los endponts

    Args:
        path (str, optional): Ruta hacia el archivo yaml. Defaults to './links.yaml'.

    Returns:
        dict: Info de los endponts
    """

    global __config

    if not __config:
        try:
            with open(path,'r') as f:   #Abro el archivo .yaml que hice, para no tener que leerlo a disco cada vez que lo llame
                __config = yaml.safe_load(f)     #Lo leo y lo inicializo a una variable
        except yaml.parser.ParserError as ex: # Error de lectura del archivo yaml
            logger.error('Error al leer el archivo .yaml')
            logger.info(ex)
        
    return __config     # En caso de que la variable _config ya etuviera inicializada , es decir ya lo hubiera leido, solo paso el valor de la variable, que es un diccionario con la info del arichivo .yaml