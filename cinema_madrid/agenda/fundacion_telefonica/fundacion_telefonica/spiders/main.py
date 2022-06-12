import scrapy 
import urllib
import subprocess
import re
import logging
import time
import datetime as dt

from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, tools
from selenium import webdriver
from requests_html import HTMLSession
session = HTMLSession()


mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

mes_pattern = re.compile(r'de ([a-z]+)')
pattern_year = re.compile(r'\d{4,4}')
pattern_schedule = re.compile(r'(\d+\sd?e?\s?(\w+)?( de \d+)?( al)?( \d+ de \w+ de \d+)?)')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

class Webscrape(scrapy.Spider):
    name = 'fundacion_telefonica'
    logger = logging.getLogger(__name__)

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    
    start_urls = ['https://www.fundaciontelefonica.com/cultura-digital/exposiciones/actuales/']


    def parse(self, response, **kwargs):
        links = response.xpath('//div[@class="column column-data"]/a/@href').getall()
        #links = set(response.xpath('//h2[@class="show-home"]/a/@href').getall()[1:])
        for idx, link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                self.logger.info(f'Link {idx}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})
    

    def get_links_by_scralling(self,url,xpath_expresion, attribute='href'):
        #Instanciar el navegador
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        #chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        driver = webdriver.Firefox(executable_path='../driver/geckodriver', options=options)
        driver.get(url)

        #Get links scralling
        box = []
        previous_heigth = driver.execute_script('return document.body.scrollHeight')
        while True:
            driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
            time.sleep(5)
            new_heigth = driver.execute_script('return document.body.scrollHeight')
            if new_heigth == previous_heigth:
                box.extend(driver.find_elements_by_xpath(xpath_expresion))
                break
            previous_heigth = new_heigth
        box = [i.get_attribute(attribute) for i in box[1:]]
        driver.close()
        return box

    def get_attribute_by_selenium(self,url,xpath_expresion,text=True,list_number=0):
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(executable_path='../driver/geckodriver', options=options)
        driver.get(url)
        time.sleep(0.5)

        if list_number == 1:
            result = driver.find_elements_by_xpath(xpath_expresion)
            result = ' '.join([i.text for i in result if i != ''])
            driver.close()
            return result
        elif list_number == 0:
            result = driver.find_elements_by_xpath(xpath_expresion)[0].text
            driver.close()
            return result

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        

        title = response.xpath('//span[@class="title"]/text()').get()
        schedule = response.xpath('//span[contains(.,"Fecha")]/following-sibling::span//text()').get()
        horario = response.xpath('//span[contains(.,"Fecha")]/following-sibling::span/text()').get()
        image = response.xpath('//div[@class="header-detail_cover"]/img/@src').get()
        description = response.xpath('//span[@class="title"]/following-sibling::p//text()').getall()
        if len(description) > 1:
            description = ' '.join(description).strip()
        else:
            description = description[0].strip()
        category = 'Exposiciones'

        #Category
        

        #schedule
        if schedule.strip() == 'Exposición permanente':
            from_date = 'Exposición permanente'
            to_date = 'Exposición permanente'
        else:
            fp, lp, from_date, to_date = get_schedule.get_schedule(schedule)

        #Image
        image_name = download_images.download_image_with_requests(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Fundación Telefónica',longitud='145.881.801',latitud='-905.017.645')
    