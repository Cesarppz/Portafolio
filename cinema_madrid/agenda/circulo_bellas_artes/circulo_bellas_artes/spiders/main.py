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
pattern_url1 = re.compile(r'https://caixaforum.org/es/madrid/familia.*')
pattern_url2 = re.compile(r'https://caixaforum.org/es/madrid/exposiciones.*')

logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
     #              datefmt='%Y-%m-%d %H:%M')


class Webscrape(scrapy.Spider):
    name = 'circulo_bellas_artes'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    start_urls = ['https://www.circulobellasartes.com/exposiciones/',
                  'https://www.circulobellasartes.com/espectaculos/',
                  'https://www.circulobellasartes.com/talleres/',
                  'https://www.circulobellasartes.com/ciclos-cine/']
    

    def parse(self, response, **kwargs):
        links = response.xpath('//div[@class="item_content"]/h4/a/@href').getall()
        #images = response.xpath('//div[@class="w-post-elm post_image usg_post_image_1 stretched"]//img/@src').getall()
        for idx, link in enumerate(links):
            if link:
                logger.info(f'Link {idx}/{len(links)}')
                #image = re.match(pattern, image).group(1)
                
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})#, 'image':images[idx]})
        

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title = response.xpath('//h1/text()').get()
        title = ' '.join([i.capitalize() for i in title.split()])
        schedule = response.xpath('//span[@class="meta_date"]//text()').get().replace('.','/').strip()
        description =  response.xpath('//h1/following-sibling::p[position()<=3]//text()').getall()
        description = ' '.join(description)
        image = response.xpath('//div[@class="entry_media"]/a/@href').get()
        category = 'Exposiciones'
        horario = 'Consultar link'
        #Category
        category = get_category.chance_category(category)

        #schedule
        print(schedule)
        schedule = [i.strip() for i in schedule.split('>')]
        print(schedule, schedule[0], schedule[-1])
        if len(schedule) <= 2 and len(schedule) > 0:
            from_date, to_date = schedule[0], schedule[-1]
        
        # _,_,from_date, to_date = get_schedule.get_schedule(schedule) 
        

        #Image
        imame_name = '_'.join([i.lower() for i in title.replace('/','_').split()]).replace('___','_').replace('__','_')
        image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=imame_name )

        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Circulo de Bellas Artes',longitud='404.183.042',latitud='-36.965.333')
    