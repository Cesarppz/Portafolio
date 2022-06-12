#!/home/cesarppz/anaconda3/envs/ws/bin/python3
import yaml
import argparse
import datetime as dt
import logging
import subprocess
from datetime import datetime
from read_yaml import read_yaml, write_yaml
from pipeline import main as pipeline_main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Scarpe-app-Add')

input_accion = '''Elige la acción a realizar
.- Add (Añadier un recinto) -> Add/A
.- Modify (Modificar un recinto) -> Modify/M
.- Delete (Eliminar un recinto) -> Delete/D
.- Count (Contar los recintos en un grupo) -> Count1/C1
.- Count (Contar todos los recintos) -> Count2/C2
.- Salir -> Exit/E '''

def add_data(file,name:str,ciclos:int,last_date_update:int,grupo) -> dict:
    file[grupo]['sitios'].append(name)
    file = modificated_ciclos(file,name,ciclos,grupo)
    file = modificated_date_update(file,name,last_date_update,grupo)
    return file
    
def modificated_ciclos(file,name,ciclos:int, grupo):
    file[grupo]['time'][name] = ciclos
    return file

def modificated_date_update(file,name,last_date_update:int, grupo):
    file[grupo]['last_scrape'][name] = last_date_update
    return file

def information():
    ciclos = input('.-Agrege cada cuantos días quiere que se ejecute el scrape \n.-Introduzca "D" para añadir el número de ciclos default (7)\n\t').capitalize()
    if ciclos == 'D':
        ciclos = 7
    try:
        ciclos = int(ciclos)
    except TypeError:
        print('El número de ciclos tiene que ser un int')
        

    last_date_update = input('.-Indique la última fecha de ejecución formato(2/12/2021 día/mes/año) \n.-Introduzca "D" para añadir la última fecha por default (Hoy)\n\t').capitalize()
    if last_date_update == 'D':
        last_date_update = dt.date.today()
    else:
        try:
            last_date_update = dt.date.today() - dt.timedelta(days=abs((datetime.strptime(last_date_update, '%d/%m/%Y') - datetime.now()).days )) 
        except:
            print('Formato inválido')
    return ciclos, last_date_update

def main(action,args):
    file = read_yaml(path='./config.yaml')
    if action == None:
        action = input(input_accion).strip().lower()

    if action == 'add' or action == 'a':
        print('\t\t - A D D - ')
        name = input('Agrege el nombre del recinto que va a añadir: ').lower().strip()
        assert (len(name.split()) == 1), '.-El nombre del recinto es invalido, no puede contener espacios'
        try:
            assert ((name not in file[args.grupo]['sitios'])), 'El recinto ya existe'
            ciclos, last_date_update = information()
            file = add_data(file,name, ciclos, last_date_update,args.grupo)
            write_yaml(file, name_file='config.yaml')
        except AssertionError as e:
            logger.error(e.args)
            choice = input('Quiere modificar este recinto? (Y/N). Si no quiere realizar una modificación presione "N" o cualquier otra tecla ').lower()
            if choice == 'y':
                ciclos, last_date_update = information()
                file = modificated_ciclos(file,name,ciclos,args.grupo)
                file = modificated_date_update(file,name,last_date_update,args.grupo)
                write_yaml(file,name_file='config.yaml')
            else:
                action = None
                main(action,args)
    elif action == 'modify' or action == 'm':
        print('\t\t - M O D I F Y - ')
        name = input('Agrege el nombre del recinto que va a modificar: ').lower().strip()
        assert (len(name.split()) == 1), '.-El nombre del recinto es invalido, no puede contener espacios'
        try:
            assert ((name in file[args.grupo]['sitios'])), 'El no recinto ya existe'
            ciclos, last_date_update = information()
            file = modificated_ciclos(file,name,ciclos,args.grupo)
            file = modificated_date_update(file,name,last_date_update,args.grupo)
            write_yaml(file,name_file='config.yaml')
            
        except AssertionError as e:
            logger.error(e.args)
            choice = input('Quiere añadir este recinto? (Y/N). Si no quiere realizar una modificación presione "N" o cualquier otra tecla ').lower()
            if choice == 'y':
                ciclos, last_date_update = information()
                file = add_data(file,name, ciclos, last_date_update,args.grupo)
                write_yaml(file, name_file='config.yaml')
            else:
                action = None
                main(action,args)
    
    elif action == 'test' or action == 't':
        print('\t\t - T E S T - ')
        book_of_index = {}                          #Un diccionario donde guardo cada indice con el nombre del recinto
        for idx, recinto in enumerate(file[args.grupo]['sitios']):
            if len(str(idx)) == 1:   #Hacer que los numeros de un solo digito esten aliniados
                print('.-','{} {:{}}'.format(recinto,idx,40-len(recinto)))
            else:
                print('.-','{} {:{}}'.format(recinto,idx,(39+len(str(idx)))-len(recinto)))
                
            book_of_index[idx] = recinto
        name = input('selecione el nombre o número del recinto que quiere testear ')

        try:                                #Si es un numero lo convierto en int, y lo busco en el diccionario de indeces, de lo contratio dejo el nombre como fue ingresado
            name = int(name)
            name = book_of_index[name]
        except ValueError:
            pass

        try:
            assert (len(name.split()) == 1), '.-El nombre del recinto es invalido, no puede contener espacios'

            if name not in file[args.grupo]['sitios']:
                logger.info('El recinto no esta entre las opciones')
                pass
            else:
                for i in file[args.grupo]['sitios']:
                    if i == name:
                        file[args.grupo]['time'][i] = 0
                    else:
                        file[args.grupo]['time'][i] = 999
                write_yaml(file,name_file='test_{}.yaml'.format(name))
                logger.info('Se ha crado el archivo de test con este nombre : {}'.format('test_{}.yaml'.format(name)))
                logger.info('Ejecutando el scraper')
                pipeline_main(args,file_test='test_{}.yaml'.format(name), test=True)
                subprocess.run(['rm','test_{}.yaml'.format(name)],cwd='.')

        except AssertionError as e:
            logger.error(e.args)
            choice = input('Quiere añadir este recinto? (Y/N). Si no quiere realizar una modificación presione "N" o cualquier otra tecla ').lower()
            if choice == 'y':
                ciclos, last_date_update = information()
                file = add_data(file,name, ciclos, last_date_update,args.grupo)
                write_yaml(file, name_file='config.yaml')
            else:
                action = None
                main(action,args)


    elif action == 'exit' or action == 'e':
        pass
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--grupo','-g',choices=['agenda'],default='agenda',type=str,help='A que grupo pertenece',nargs='?')
    parser.add_argument('--action','-a',default='add',choices=['add','modify','test'],type=str,help='Qué acción se va a realizar',nargs='?')
    parser.add_argument('--system','-s',default='linux',choices=['linux','windows'],type=str,help='En que sistema esta corriendo el programa',nargs='?')
    args = parser.parse_args()
    main(args.action,args)