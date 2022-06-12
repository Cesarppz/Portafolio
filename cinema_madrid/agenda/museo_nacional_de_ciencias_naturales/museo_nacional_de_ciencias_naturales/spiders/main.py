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
pattern_url1 = re.compile(r'https://caixaforum.org/es/madrid/familia.*')
pattern_url2 = re.compile(r'https://caixaforum.org/es/madrid/exposiciones.*')

logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
     #              datefmt='%Y-%m-%d %H:%M')


class Webscrape(scrapy.Spider):
    name = 'museo_nacional_de_ciencias_naturales'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    start_urls = ['https://www.mncn.csic.es/es/visita-el-mncn/exposiciones/buscar?field_fecha_inicio_value_1=&field_fecha_fin_value=&field_finConInicio=&field_inicioConFin=&body=&title=&tags=&sala=&tipodeexposicion=Temporal']
    

    def parse(self, response, **kwargs):
        links = response.xpath('//div[@class="bigImageResult__item"]/a/@href').getall()
        #images = response.xpath('//div[@class="w-post-elm post_image usg_post_image_1 stretched"]//img/@src').getall()
        for idx, link in enumerate(links):
            if link:
                logger.info(f'Link {idx}/{len(links)}')
                #image = re.match(pattern, image).group(1)
                link = 'https://www.mncn.csic.es/{}'.format(link)
                
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})#, 'image':images[idx]})
        

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title = response.xpath('//h1//text()').get()
        title = ' '.join([i.capitalize() for i in title.split()])
        schedule = response.xpath('//div[@class="activities__descripcion"]/p[position()=1]/strong//text()').get()
        horario = 'Revisar link'
        description = response.xpath('//div[@class="activities__descripcion"]/p/text()').getall()
        description = ' '.join(description)
        image = response.xpath('//div[@class="content"]/@style').get()
        image = re.match(patter_style,image).group(1)
        image = 'https://www.mncn.csic.es/{}'.format(image)
        category = 'Exposiciones'
        print(image)

        #Category
        category = get_category.chance_category(category)

        #schedule
        if schedule:
            _,_,from_date, to_date = get_schedule.get_schedule(schedule) 
        else:
            from_date, to_date = 'Consultar link', 'Consultar link'
        

        #Image
        imame_name = '_'.join([i.lower() for i in title.replace('/','_').split()]).replace('___','_').replace('__','_')
        image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=imame_name )

        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Museo Nacional de Ciencias Naturales',longitud='404.409.237',latitud='-3.689.709.299.999.990')
    