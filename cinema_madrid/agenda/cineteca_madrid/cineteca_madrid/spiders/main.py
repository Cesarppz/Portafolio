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
pattern_year = re.compile(r'\d{4,4}')
pattern_schedule = re.compile(r'(\d+\sd?e?\s?(\w+)?( de \d+)?( al)?( \d+ de \w+ de \d+)?)')
pattern = re.compile(r'(^http.*\.\w{3})(.*)')
patter_style = re.compile(r'background-image:url\((.*\.\w{3}).*')


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
     #              datefmt='%Y-%m-%d %H:%M')


class Webscrape(scrapy.Spider):
    name = 'cineteca_madrid'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    start_urls = ['https://www.cinetecamadrid.com/programacion?s=&to=2021-12-27&since=&page=0']

    def parse(self, response, **kwargs):
        links = response.xpath('//h2/a/@href').getall()
        if links:
            for idx, link in enumerate(links):
                if link:
                    logger.info(f'Link {idx}/{len(links)}')
                    #image = re.match(pattern, image).group(1)
                    link = 'https://www.cinetecamadrid.com{}'.format(link)
                    
                    yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})#, 'image':images[idx]})
            
        next_page = response.xpath('//li[@class="pager__item pager__item--next"]/a/@href').get() 
        if next_page:
            next_page = 'https://www.cinetecamadrid.com/programacion{}'.format(next_page)
            yield response.follow(next_page, callback=self.parse)
        

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title = remove_blank_spaces(response.xpath('//h2[@class="title"]/text()').get())
        schedule = []
        # print('Schedule: ',schedule)
        horario = 'Revisar link'
        description = response.xpath('//div[@class="field field-name-field-description"]/p//text()').getall()
        description = remove_blank_spaces(' '.join(description))
        image =  response.xpath('//div[@class="field field-name-field-outstanding-image"]/img/@src').get()
        if image:
            image = 'https://www.cinetecamadrid.com{}'.format(image)
        else:
            image = response.xpath('//div[@class="field field-name-field-images"]/a/@href').getall()
            image = image[random.randint(0, len(image)-1)]

        
        category = 'cine'
        print('Image: ',image)

        #Category
        category = get_category.chance_category(category)

        #schedule

        if schedule:
           from_date, to_date = schedule[0],schedule[-1]
        else:
           from_date, to_date = 'Consultar link', 'Consultar link'
        

        #Image
        imame_name = '_'.join([i.lower() for i in remove_blank_spaces(title).replace('/','_').split()]).replace('___','_').replace('__','_')
        image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=imame_name )
        
        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Cineteca Madrid',longitud='403.917.766',latitud='-36.973.165')
        
