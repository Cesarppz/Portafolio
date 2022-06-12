#!/home/cesarppz/anaconda3/envs/ws/bin/python3
import yaml 

__config = None

def read_yaml(path='./config.yaml'):
    global __config

    if not __config:
        with open(path,'r') as f:   #Abro el archivo .yaml que hice, para no tener que leerlo a disco cada vez que lo llame
            __config = yaml.safe_load(f)     #Lo leo y lo inicializo a una variable
        
    return __config     # En caso de que la variable _config ya etuviera inicializada , es decir ya lo hubiera leido, solo paso el valor de la variable, que es un diccionario con la info del arichivo .yaml

def write_yaml(yaml_file,name_file='config.yaml'):
    with open(name_file,'w') as f:
        yaml.safe_dump(yaml_file,f)