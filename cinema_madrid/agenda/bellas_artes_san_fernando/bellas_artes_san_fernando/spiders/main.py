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
    name = 'bellas_artes_san_fernando'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    start_urls = ['https://www.centrocentro.org/exposiciones']
    

    def parse(self, response, **kwargs):
        links = response.xpath('//li//h4/a/@href').getall()
        links = [i.replace('\\','').replace('"','').replace('https://www.realacademiabellasartessanfernando.com/es/actividades/exposiciones/more/','') for i in links]
        #images = response.xpath('//div[@class="w-post-elm post_image usg_post_image_1 stretched"]//img/@src').getall()
        if links:
            for idx, link in enumerate(links):
                if link:
                    logger.info(f'Link {idx}/{len(links)}')
                    #image = re.match(pattern, image).group(1)
                    #link = 'https{}'.format(link)
                    
                    yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})#, 'image':images[idx]})
            
        next_page = 'https://www.realacademiabellasartessanfernando.com/es/actividades/exposiciones/more/{}'
        for i in range(1,25):
            page = next_page.format(i)
            yield response.follow(page,callback=self.parse)


    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title = remove_blank_spaces(' '.join(response.xpath('//div[@class="titulo_enimagen"]/h3/text()').getall()))
        title = ' '.join([i.capitalize() for i in title.split()])
        schedule = remove_blank_spaces(response.xpath('//div[@class="titulo_enimagen"]/span/text()').get().split('/')[-1])
        horario = 'Revisar link'
        description = response.xpath('//div[@class="cuerpo_texto"][position()=1]//text()').getall()
        description = remove_blank_spaces(' '.join(description))
        image = response.xpath('//div[@class="imagen_cabecera_contitulo "]/img/@src').get()
        category = 'Exposiciones'

        #Category
        category = get_category.chance_category(category)

        #schedule

        if schedule:
            _,_,from_date, to_date = get_schedule.get_schedule(schedule) 
        else:
            from_date, to_date = 'Consultar link', 'Consultar link'
        

        #Image
        imame_name = '_'.join([i.lower() for i in remove_blank_spaces(title).replace('/','_').split()]).replace('___','_').replace('__','_')
        image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=imame_name )
        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Real Academia Bellas Artes de San Fernando',longitud='404.179.334',latitud='-3.700.740.699.999.990')
        