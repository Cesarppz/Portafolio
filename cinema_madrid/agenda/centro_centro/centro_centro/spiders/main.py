from shutil import ExecError
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
    name = 'centro_centro'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    start_urls = ['https://www.centrocentro.org/exposiciones']
    

    def parse(self, response, **kwargs):
        links = response.xpath('//div[@class="image-holder"]//a/@href').getall()
        #images = response.xpath('//div[@class="w-post-elm post_image usg_post_image_1 stretched"]//img/@src').getall()
        for idx, link in enumerate(links):
            if link:
                logger.info(f'Link {idx}/{len(links)}')
                #image = re.match(pattern, image).group(1)
                link = 'https://www.centrocentro.org{}'.format(link)
                
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})#, 'image':images[idx]})
        

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title = remove_blank_spaces(response.xpath('//div[@class="field field-name-node-title"]/h2/text()').get())
        title = ' '.join([i.capitalize() for i in title.split()])
        schedule = remove_blank_spaces(response.xpath('//div[@class="programacion"]/div[@class="field field-name-field-schedule-tip"]/text()').get().replace('.','/'))
        horario = remove_blank_spaces(' '.join(response.xpath('//div[@class="programacion"]/div[@class="field field-name-field-schedule-txt"]//text()').getall()))
        description = response.xpath('//div[@class="field field-name-field-description"]/p[position()<=3]//text()').getall()
        description = ' '.join(description)
        image = response.xpath('//div[@class="field field--name-field-outstanding-image field--type-image field--label-hidden field__item"]/img/@src').get()
        image = 'https://www.centrocentro.org{}'.format(image)
        category = 'Exposiciones'

        #Category
        category = get_category.chance_category(category)

        #schedule
        print(schedule)
        from_date, to_date = remove_blank_spaces(schedule.split('-')[0]), remove_blank_spaces(schedule.split('-')[1])


        if len(from_date.split('/')) == 2 and str(to_date.split('/')[-1]) == str(year - 1):
            raise StopIteration

        elif len(from_date.split('/')) == 2:
            from_date = '{}/{}'.format(from_date,to_date.split('/')[-1])


        # if schedule:
        #     _,_,from_date, to_date = get_schedule.get_schedule(schedule) 
        # else:
        #     from_date, to_date = 'Consultar link', 'Consultar link'
        

        #Image
        print(image)
        imame_name = '_'.join([i.lower() for i in remove_blank_spaces(title).replace('/','_').split()]).replace('___','_').replace('__','_')
        image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=imame_name )
        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Centro Centro',longitud='404.190.383',latitud='-36.920.752')
        