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
    name = 'sala_arte_canal_isabel_ii'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    start_urls = ['https://www.comunidad.madrid/centros/sala-canal-isabel-ii']

    def parse(self, response, **kwargs):
        links = response.xpath('//div[@id="programacion-canal"]/div[@id="paragraphs_item_column_full_group_paragraph"]//div[@class="field-item even"]/span[@class="h3"]/a/@href').getall()
        if links:
            for idx, link in enumerate(links):
                if link:
                    logger.info(f'Link {idx}/{len(links)}')
                    link = 'https://www.comunidad.madrid{}'.format(link)   
                    yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+2,'len':len(links)})#, 'image':images[idx]})
            
        # next_page = response.xpath('//li[@class="next"]/a/@href').get()
        # if next_page:
        #     yield response.follow(next_page, callback=self.parse)
        

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
       
        # response_session = session.get(link_schedule).html

        title = response.xpath('//h1//text()').get()
        schedule = ' '.join(response.xpath('//div[@class="field-item even"]/child::span[@class="date-display-range"]/..//text()').getall())
        # print('Schedule: ',schedule)
        horario = 'Consultar link'
        description = response.xpath('//div[@class="field-item even"][@property="schema:description"]/p//text()').getall()
        description = remove_blank_spaces(' '.join(description))
        image =  response.xpath('//div[@class="item-0 item-odd"]/img/@src').get()
        # image = 'http://www.museolazarogaldiano.es/{}'.format(image)
        category = 'Fotografía'

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
        image_name = download_images.download_image_with_requests_without_format(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=imame_name )
        
        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Sala de Arte Canal Isabel II',longitud='404.395.402',latitud='-37.012.875')
        