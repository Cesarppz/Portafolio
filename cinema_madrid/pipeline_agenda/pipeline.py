#!/home/cesarppz/anaconda3/envs/ws/bin/python3
import subprocess
import logging
import datetime as dt
import os
import sys
import argparse
import re

from read_yaml import  read_yaml, write_yaml
from datetime import datetime
from cancat import concat_dataframes, concat_images

# Fecha de hoy
dia = datetime.now().day
mes = datetime.now().month
# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Scarpe-app')


def write_output(out, path_file='./scraper.log'):
    with open(path_file, 'ab') as f:
        f.write(out)


def run_program(path,path_final_dir,flag):
    #os.chdir('/home/cesarppz/Documents/jobs/agenda/cine_paz')
    logger.info('Scraping {} ...'.format(flag))
    try:
        try:
            command = subprocess.Popen(['scrapy','crawl',flag,'--loglevel','INFO'],cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _ , logs = command.communicate()
            # command.wait()
            if command.returncode != 0:
                try:
                    command2 = subprocess.Popen(['python3',f'{flag}.py'],cwd=path,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, logs = command2.communicate()
                    if command2.returncode == 0:
                        logger.info('Comando exitoso')
                        write_output(bytes('\n\nLogs del scrape {}\n'.format(flag), encoding='utf-8'))
                        write_output(out)
                        write_output(logs)  
                    else:
                        raise SystemError
                except SystemError:
                    write_output(bytes('\n\nLogs del scrape {}\n'.format(flag), encoding='utf-8'))
                    logger.error('Error en el comando')
                    write_output(logs)
            else:
                write_output(bytes('\n\nLogs del scrape {}\n'.format(flag), encoding='utf-8'))
                logger.info('Comando exitoso')
                write_output(logs)

            if 'results_{}_{}_{}.csv'.format(flag,dia,mes) not in os.listdir(path+'/'):
                raise FileNotFoundError
        except FileNotFoundError :
            logging.error('No se produjo ningún archivo')
        except Exception as ex:
            print(ex)

        logger.info('Scrape finalizado satifactoriamente')

    except Exception as exc:
        logger.warning('Error en el Scrape {} - {}'.format(flag,exc))
    
    try:
        if 'results_{}_{}_{}.csv'.format(flag,dia,mes) in os.listdir(path+'/') and 'data_{}_{}_{}'.format(flag,dia,mes) in os.listdir(path+'/'):
            subprocess.run(['mv','results_{}_{}_{}.csv'.format(flag,dia,mes),path_final_dir],cwd=path)
            subprocess.run(['mv','data_{}_{}_{}/'.format(flag,dia,mes),path_final_dir],cwd=path)
            logger.info('Archivos movidos satifactoriamente')
        else :
            raise FileExistsError('No se encuentra los archivos a mover - {}'.format(flag))
    except FileExistsError as fx:
        logger.warning('Error {} en {}'.format(fx,flag))
        

def main(args, file_test = None, test=False):
    if file_test:
        if re.match(r'test.*.yaml',file_test):
            yaml = read_yaml(args)
    else:
        if args.test:
            yaml = read_yaml(args.test)
        else:
            yaml = read_yaml()
    lista_sitios = yaml['agenda']['sitios']
    today = dt.date.today()
    for idx, site in enumerate(lista_sitios):
        last_scrape = yaml['agenda']['last_scrape'][site]
        time_to_screpe = yaml['agenda']['time'][site]
        days_to = last_scrape - today

        if abs(days_to.days) >= time_to_screpe: #Si han pasado la cantidad de dias definida en el archivo yaml o más, se aplicara el scrape
            logger.info('Sitio {}/{}'.format(idx+1,len(lista_sitios)))

            if args.system == 'windows':  #Segun el sistema operativo donde este, se cambia la carpeta 
                path = '/home/cesarppz/Documents/jobs/agenda/{}'.format(site)
                path_final_dir = '//mnt/c/Users/cesar/Desktop/fiver_javier/'
            else:
                path = '/home/cesar/Documents/job/web_scraping/javier/agenda/{}'.format(site)
                path_final_dir = '/home/cesar/Desktop/javier_fiverr/'

            run_program(path,path_final_dir,site)
            yaml['agenda']['last_scrape'][site] = today
            if test == False:
                write_yaml(yaml)
        else:
            logger.info('Faltan {} para scrapear {}'.format(time_to_screpe - abs(days_to.days),site))
    try:
        concat_dataframes(path_folder=path_final_dir)
        logger.info('Data Frames concatenados con exito')
        concat_images(path_folder=path_final_dir)
    except Exception as ex:
        print(ex)
        logger.warning('Se ha producido un error al concatenar los data frames')

        
    
    # subprocess.run(['scrapy','crawl','cine_paz'],cwd='./agenda/cinepaz/')
    # subprocess.run(['mv','results_cine_paz_{}_{}.csv'.format(dia,mes),'//mnt/c/Users/cesar/Desktop/'],cwd='./agenda/cinepaz/')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test','-t',type=str,help='Test es para hacer el test de uno o más recintos',nargs='?')
    parser.add_argument('--system','-s',default='linux',choices=['linux','windows'],type=str,help='En que sistema esta corriendo el programa',nargs='?')
    args = parser.parse_args()
    main(args)