import scrapy 
import urllib
import subprocess
import re
import logging
import time
import datetime as dt

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
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
     #              datefmt='%Y-%m-%d %H:%M')


class Webscrape(scrapy.Spider):
    name = 'museo_arte_contemporaneo'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    start_urls = ['https://www.madrid.es/portales/munimadrid/es/Inicio/Contacto/Direcciones-y-telefonos/Museo-de-Arte-Contemporaneo?vgnextfmt=default&vgnextoid=d6b0744554b6b010VgnVCM100000d90ca8c0RCRD&vgnextchannel=bfa48ab43d6bb410VgnVCM100000171f5a0aRCRD#']
    

    def parse(self, response, **kwargs):
        links = response.xpath('//div[@class="news-body"]/h4/a/@href').getall()
        #images = response.xpath('//div[@class="w-post-elm post_image usg_post_image_1 stretched"]//img/@src').getall()
        for idx, link in enumerate(links):
            if link:
                logger.info(f'Link {idx}/{len(links)}')
                #image = re.match(pattern, image).group(1)
                link = 'https://www.madrid.es{}'.format(link)
                
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})#, 'image':images[idx]})
        

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title = response.xpath('//h3[@class="summary-title"]/text()').get()
        title = ' '.join([i.capitalize() for i in title.split()])
        schedule = response.xpath('//h4[@class="fecha title9"]/following-sibling::p/text()').get()
        horario = 'Revisar link'
        description = response.xpath('//div[@class="tiny-text"]/p[position()<=3]//text()').getall()
        description = ' '.join(description)
        image = response.xpath('//div[@class="image-content ic-right"]/img/@src').get()
        if image is None:
            image = response.xpath('//div[@class="generic-content"]//img/@src').get()
        image = 'https://www.madrid.es{}'.format(image)
        category = 'Arte'

        #Category
        category = get_category.chance_category(category)

        #schedule
        if schedule:
            _,_,from_date, to_date = get_schedule.get_schedule(schedule) 
        else:
            from_date, to_date = 'Consultar link', 'Consultar link'
        

        #Image
        print(image)
        imame_name = '_'.join([i.lower() for i in remove_blank_spaces(title).replace('/','_').split()]).replace('___','_').replace('__','_')
        image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=imame_name )

        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Museo Arte Contemporaneo',longitud='407.582.089',latitud='-7.399.861.039.999.990')
    