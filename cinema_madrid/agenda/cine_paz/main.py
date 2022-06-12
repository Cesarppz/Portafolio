from selenium import webdriver
import logging
import time
from selenium.common.exceptions import NoSuchElementException
from move_image import move_image_to_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Scraper')

url = 'https://www.cinepazmadrid.es/es/cartelera'


def _back_page(driver):
    driver.back()
    time.sleep(5)


def single_page(driver):
    n = 0
    horario = []
    try: 
        while True:
            day = driver.find_element_by_xpath(f'//div[@class="contenedor_horarios"]/div[@data-num={n}]')
            logger.info('Haciendo click en los dias')
            try:
                day.click()
            except Exception as e:
                logger.error(e)
            day_text = day.text
            logger.info(f'Haciendo click en {day_text}')
            time = driver.find_elements_by_xpath(f'//div[@class="contenedor_cines cines_ficha clearfix cines-{n}"]//div[@class="horas"]//a[@class="btn btn-default metrica"]')
            horario.extend([day_text,[t.text for t in time]])
            if n==0:
                buy_link = time[0].get_attribute('href')
            n += 1
    except NoSuchElementException as element :
        logger.error('No more elements')
    
    #Title
    logger.info('Finding title')
    title = driver.find_element_by_xpath('//div[@class="row marginL0 marginR0"]/div[@class="text-header2 gibsonT"]/span').text
    logger.info(f'The title is {title}')
    final_title = f'Cine paz / {title} / {horario[0]}-{horario[-2]}'
    #Sinopsis
    logger.info('Finding sinopsis')
    sinopsis = driver.find_element_by_xpath('//div[@class="col-xs-12 paddingL0 paddingR0"]/span[@class="sinopsis gibsonL"]').text
    #Image 
    logger.info('Finding Image')
    image_link = driver.find_element_by_xpath('//div[@class="col-xs-5 relativo"]//img').get_attribute('src')
    move_image_to_dir(image_link)

    logger.info('Go back')
    #_back_page(driver)
    
    return {'Desde': horario[0],
            'Hasta' : horario[-2],
            'title':final_title, 
            'Descricion':sinopsis,
            'Hours':horario,
            'buy_link':buy_link}


def get_links(driver):
    time.sleep(1.5)
    links = driver.find_elements_by_xpath('//div[@class="col-md-8 events-column izquierda clearfix"]//div[@class="col-sm-8 col-xs-7"]//a')
    logger.info('Getting the main links')
    
    big_box = []
    for idx, link in enumerate(links):
        time.sleep(3)
        print('buscando')
        if idx == 0:
            try: 
                driver.get(link.get_attribute('href'))
                data = single_page(driver)
                big_box.append(data)
                driver.close()
            except Exception as e:
                logger.error(e)
                driver.close()
        else:
            try: 
                driver = _open_browser()
                driver.get(link.get_attribute('href'))
                data = single_page(driver)
                big_box.append(data)
                driver.close()
            except Exception as e:
                logger.error(e)
                driver.close()
        
    
    return big_box
        

def _get_url(driver,url):
    try:
        driver.get(url)
        logger.info('Making get to url (%s)' % url)
        return driver
    except Exception as e:
        logger.error('Failed making get to url (%s)' % url, e)

def _open_browser():
    options = webdriver.ChromeOptions()
    options.add_argument(r'--user-data-dir=/home/cesar/.config/google-chrome/default/Default')

    try:
        driver = webdriver.Chrome(executable_path='/home/cesar/Desktop/whts/driver/chromedriver', options=options)
        logger.info('Navegador Instanciado')
        return driver
    except Exception as e:
        logger.error('Failed to open browser',e)

def main():
    driver = _open_browser()
    driver = _get_url(driver,url)
    main_links = get_links(driver) 



if __name__ == '__main__':
    main()