from shutil import ExecError
import scrapy 
import urllib
import subprocess
import re
import logging
import time
import datetime as dt
import random

from datetime import datetime
from scrapy_splash import SplashRequest
from agenda_tools import get_schedule, download_images, get_category, tools
from agenda_tools.get_schedule import remove_blank_spaces
from selenium import webdriver
from requests_html import HTMLSession
session = HTMLSession()


mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

mes_pattern = re.compile(r'de ([a-z]+)')
# pattern_year = re.compile(r'\d{5,4}')
pattern_schedule = re.compile(r'(\d+\sd?e?\s?(\w+)?( de \d+)?( al)?( \d+ de \w+ de \d+)?)')
pattern = re.compile(r'(^http.*\.\w{4})(.*)')
patter_style = re.compile(r'background-image:url\((.*\.\w{4}).*')


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
     #              datefmt='%Y-%m-%d %H:%M')


class Webscrape(scrapy.Spider):
    name = 'bibloteca_nacional'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    start_urls = ['http://www.bne.es/es/Actividades/Exposiciones/Proximaexpo/']

    def parse(self, response, **kwargs):
        links = response.xpath('//div[@class="enlaceTextoImagen"]//ul//a/@href').getall()
        if links:
            for idx, link in enumerate(links):
                if link:
                    logger.info(f'Link {idx}/{len(links)}')
                    link = 'http://www.bne.es{}'.format(link)   
                    yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+2,'len':len(links)})#, 'image':images[idx]})
            
        # next_page = response.xpath('//li[@class="next"]/a/@href').get()
        # if next_page:
        #     yield response.follow(next_page, callback=self.parse)
        

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
       
        # response_session = session.get(link_schedule).html

        title = response.xpath('//h2[@class="rs_leer"]//text()').get()
        schedule = response.xpath('//li[@class="horario"]/p/text()').get()
        # print('Schedule: ',schedule)
        horario = response.xpath('//li[@class="horario"]/p[2]/text()').getall()
        horario = ' '.join(horario)
        if horario is None:
            horario = 'Consultar link'
        description = response.xpath('//div[@class="text_plain noborder"]/p[1]//text()').getall()
        description = remove_blank_spaces(' '.join(description))
        description = description.replace(schedule,'').strip()
        image =  response.xpath('//div[@class="img_lista"]//img/@src').get()
        image = 'http://www.bne.es{}'.format(image)
        # image = 'http://www.museolazarogaldiano.es/{}'.format(image)
        category = 'Exposiciones'

        #Category
        category = get_category.chance_category(category)

        #schedule
        print('S:',schedule)
        if schedule:
           _, _ , from_date, to_date = get_schedule.get_schedule(schedule)
        else:
           from_date, to_date = 'Consultar link', 'Consultar link'
        

        #Image
        imame_name = '_'.join([i.lower() for i in remove_blank_spaces(title).replace('/','_').split()]).replace('___','_').replace('__','_')
        image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=imame_name )
        
        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Biblioteca Nacional',longitud='361.522.744',latitud='-959.465.575')
        