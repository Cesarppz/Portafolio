#!/usr/bin/python3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from reading import read
from class_day import check_date
from radical_week import check_week
import argparse
import time
import logging
url = 'https://web.whatsapp.com/'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Cron-app')


def chats_of_the_day(destination, path):
    day_groups = check_date(destination, path)
    return day_groups


def _load_data(destination, path):
    data = read(path)
    if destination == 'G':
        destination = 'groups'
    elif destination == 'P':
        destination = 'persons'

    data_names = data[destination] 
    return data_names


def _open_browser():
    # Setear las opciones del navegador
    options = webdriver.ChromeOptions()
    options.add_argument(r'--user-data-dir=/home/cesar/.config/google-chrome/default/Default')
    options.add_argument('--profile-directory=Default')
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument(r'--user-data-dir=/home/cesar/.config/google-chrome/default/Default')
    # options.add_argument('--profile-directory=Default')
    # options.add_argument('--no-sandbox')

    #Instancear el navegador
    try:
        driver = webdriver.Chrome(executable_path='/home/cesar/Desktop/whts/driver/chromedriver', options=options)
        logger.info('Navegador instanciado')
        time.sleep(5)
        try:
            driver.get(url)
            logger.info('Haciedno get a la url')
            return driver
        except Exception as e:
            logger.error('Ha ocurrido un error al traer la url:',e)
    except Exception as e:
        logger.error('Ha ocurrido un error al instanciar el navegador:',e)

def _find_chat(driver,name):
    time.sleep(3)
    try:
        logger.info('Buscando chat')
        find_chats = driver.find_element_by_xpath('//div[@role="textbox"]')
        find_chats.click()
        find_chats.send_keys(name + Keys.ENTER)
    except Exception as e:
        input('Si ya estas loggeado en whatsapp oprime enter')
        logger.warning('Error al buscar el chat')
        logger.error(e)
        _close(driver)
        raise e('Error al buscar el chat')

    
def _write_message(driver,message):
    chat_open = False 
    while chat_open == False:
        try:
            main_box = driver.find_element_by_xpath('//div[@class="_1SEwr"]')
            main_box.click()
            text_box = driver.find_element_by_xpath('//div[@class="_1SEwr"]//div[@role="textbox" and @class="_13NKt copyable-text selectable-text"]')
            text_box.send_keys(message + Keys.ENTER)
            logger.info('Se ha enviado el mensaje')

            chat_open = True
    
        except NoSuchElementException as element_not_found:
            logger.warning('Cragando el chat')
            time.sleep(300)
            continue
        except Exception as e:
            logger.error('Error al buscar la box main del chat')
            logger.error(e)
            break

    
def _close(driver):
    driver.close()


def main(destination, yaml_path, radical_path):
    data_groups = _load_data(destination, yaml_path)
    radical_week = check_week(radical_path)

    if radical_week:
        driver = _open_browser()
        true_chats = chats_of_the_day(destination, yaml_path)
        for name, message in data_groups.items():
            if name  in true_chats: #Verificar si hay que mandar el mensaje al chat ese dia 
                _find_chat(driver, name)
                _write_message(driver, message[0])
                time.sleep(2)
        _close(driver)
    else:
        logger.info('Estamos en semana precencial')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Enviar mensaje a un grupo o personalizado")
    parser.add_argument(
        '--Destination',
        type=str,
        help='Seleciona G/grupo para enviar el mensaje a un grupo, si lo quieres mandar a un único destnatario selecciona P/persona',
        choices=['G','groups','persons','P'],
        default='G')
    parser.add_argument(
        '--yaml_path',
        type=str,
        help='Proporciona la ruta hacia el archivo yaml',
        default='./config.yaml')
    parser.add_argument(
        '--radical_path',
        help='Proporciona la ruta hacia el archivo de conteo de semanas',
        default='./radical_week.txt'
    )
    args = parser.parse_args()
    main(args.Destination,args.yaml_path,args.radical_path)
