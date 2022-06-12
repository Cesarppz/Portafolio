#encoding=utf-8
import scrapy 
import re
import logging
import datetime as dt
import time
import random

from selenium.common.exceptions import NoSuchElementException
from requests_html import HTMLSession
from selenium import webdriver
from scrapy_splash import SplashRequest
from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, months
from agenda_tools.get_schedule import remove_blank_spaces

session = HTMLSession()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_eng_adv = months.dict_of_months_adv_spanish_to_english 

pattern = re.compile(r'\w+. \w+. \d+')
pattern_schedule = re.compile(r'((\d+,\s)?\d+\sd?e?\s?(\w+.?)?( de \d+)?( al)?( y)?( \d+\s?d?e? \w+.?\,?\s?d?e?\s?(\d+)?)?)')
pattern_extract_images = re.compile(r'\((http.://teatrodelbarrio.com/.*)\)')
#comma_schedule =  re.compile(r'\d+, \d+')
#url_category_pattern = re.compile(r'^https.*/(.*)$')
#base_url = 'https://www.teatroreal.es'


class Webscrape(scrapy.Spider):
    name = 'museo_sorolla'
    logger = logging.getLogger(name)

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }


    def start_requests(self):
        url = ['https://www.culturaydeporte.gob.es/msorolla/exposicion/sorolla-viaja.html',
               'https://www.culturaydeporte.gob.es/msorolla/exposicion/exposicion-permanente.html',
               'https://www.culturaydeporte.gob.es/msorolla/exposicion/exposiciones-temporales.html']

        for u in url:
            yield scrapy.Request(u,self.parse)

    def parse(self, response):
        link = response.request.url
        category = 'Exposiciones'
        id_category = get_category.id_category(category)
        main_category = get_category.main_category(category)

        if link == 'https://www.culturaydeporte.gob.es/msorolla/exposicion/sorolla-viaja.html':
            titles = response.xpath('//div[@class="cte"]/h2//text()').getall()
            schedules = response.xpath('//div[@class="cte"]/h2/following-sibling::p[@class="ta-justify"][1]//text()').getall()
            description = response.xpath('//div[@class="cte"]/p/following-sibling::p[@class="ta-justify"][position()>=3]//text()').getall()
            images = response.xpath('//div[@class="cim gr izquierda "]/img/@src').getall()
            horario = None

            for idx, i in enumerate(titles):
                print('Image :','https://www.culturaydeporte.gob.es{}'.format(images[idx]).replace(".jpg",'',1).replace(".png",'',1))
                image_name = download_images.download_opener('https://www.culturaydeporte.gob.es{}'.format(images[idx]).replace(".jpg",'',1).replace(".png",'',1).replace(".JPG",'.jpg'),nombre_del_lugar=self.name,idx=idx,len_links=len(titles))
                print('Image :',image_name)
                fp, lp, from_date, to_date = get_schedule.get_schedule(schedules[idx])
                yield { 
                    'From':from_date,
                    'To':to_date,
                    # 'Desde':fp,
                    # 'Hasta': lp,
                    'title/Product_name': titles[idx].capitalize(),
                    'Place_name/address':'Museo Sorolla',
                    'Categoria' : category,
                    'Title_category':main_category,
                    'Nº Category': id_category,
                    'image':image_name,
                    'Hours':horario,
                    'Link_to_buy': link,
                    'Description':description,
                    #'Area': 'Salamanca ',
                    'City': 'Madrid',
                    'Province': 'Madrid',
                    'Country':'España',
                    'latitud':'404.354.306',
                    'longitud':'-36.925.053',	
                    'Link':link
                    
                    }
        elif link == 'https://www.culturaydeporte.gob.es/msorolla/exposicion/exposicion-permanente.html':
            images = response.xpath('//div[@class="enlace "]/img/@src').getall()
            images = ['https://www.culturaydeporte.gob.es{}'.format(image) for image in images]
            titles = response.xpath('//div[@class="enlace "]/p[@class="titulo"]//text()').getall()
            description = response.xpath('//div[@class="enlace "]/p[@class="descripcion"]//text()').getall()
            from_date = 'Permanente'
            to_date = 'Permanente'
            horario = None
            for idx, i in enumerate(images):
                image_name = download_images.download_opener(images[idx].replace(".jpg",'',1).replace(".png",'',1).replace(".JPG",'.jpg'),nombre_del_lugar=self.name,idx=idx,len_links=len(titles))
                yield { 
                    'From':from_date,
                    'To':to_date,
                    # 'Desde':fp,
                    # 'Hasta': lp,
                    'title/Product_name': titles[idx].capitalize(),
                    'Place_name/address':'Museo Sorolla',
                    'Categoria' : category,
                    'Title_category':main_category,
                    'Nº Category': id_category,
                    'image':image_name,
                    'Hours':horario,
                    'Link_to_buy': link,
                    'Description':description,
                    #'Area': 'Salamanca ',
                    'City': 'Madrid',
                    'Province': 'Madrid',
                    'Country':'España',
                    'latitud':'404.354.306',
                    'longitud':'-36.925.053',	
                    'Link':link
                    
                    }

        elif link == 'https://www.culturaydeporte.gob.es/msorolla/exposicion/exposiciones-temporales.html':
            images = response.xpath('//div[@class="cim md formato-r"]/img/@src').getall()
            images = ['https://www.culturaydeporte.gob.es{}'.format(image) for image in images]
            title = response.xpath('//h2[@class="ta-center"]//text()').get()
            fp, lp, from_date, to_date = get_schedule.get_schedule(response.xpath('//h2[@class="ta-center"]/following-sibling::p[2]//text()').get())
            image_name = download_images.download_opener(images[random.randint(0,len(images))].replace(".jpg",'',1).replace(".png",'',1).replace(".JPG",'.jpg'),nombre_del_lugar=self.name,idx=0,len_links=1)
            horario = None
            description = ' '.join(response.xpath('//div[@class="cte"][2]/p//text()').getall())
            yield { 
                    'From':from_date,
                    'To':to_date,
                    # 'Desde':fp,
                    # 'Hasta': lp,
                    'title/Product_name': title.capitalize(),
                    'Place_name/address':'Museo Sorolla',
                    'Categoria' : category,
                    'Title_category':main_category,
                    'Nº Category': id_category,
                    'image':image_name,
                    'Hours':horario,
                    'Link_to_buy': link,
                    'Description':description,
                    #'Area': 'Salamanca ',
                    'City': 'Madrid',
                    'Province': 'Madrid',
                    'Country':'España',
                    'latitud':'404.354.306',
                    'longitud':'-36.925.053',	
                    'Link':link
                    
                    }