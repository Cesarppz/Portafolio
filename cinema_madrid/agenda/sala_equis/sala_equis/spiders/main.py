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
logger.setLevel(logging.INFO)
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
     #              datefmt='%Y-%m-%d %H:%M')


class Webscrape(scrapy.Spider):
    name = 'sala_equis'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    def start_requests(self):
        url = 'https://salaequis.es/taquilla/'

        yield SplashRequest(url=url, callback=self.parse )
    

    def parse(self, response, **kwargs):
        links = response.xpath('//div[@class="title bigFont"]/a/@href').getall()
        #images = response.xpath('//div[@class="w-post-elm post_image usg_post_image_1 stretched"]//img/@src').getall()
        if links:
            for idx, link in enumerate(links):
                if link:
                    logger.info(f'Link {idx}/{len(links)}')
                    #image = re.match(pattern, image).group(1)
                    #link = 'https{}'.format(link)
                    
                    yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})#, 'image':images[idx]})
            

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title = remove_blank_spaces(response.xpath('//div[@class="summary entry-summary"]/h1/text()').get())
        url_schedule = response.xpath('//div[@class="woocommerce-product-details__short-description"]/a/@href').get()
        schedule = tools.get_attribute_by_selenium(url =url_schedule,xpath_expresion='//div[@class="row  no-gutters shadow-lg border rounded"]/div[1]',list_number=1 )
        schedule = [remove_blank_spaces(i) for i in schedule.split()]
        schedule = schedule[1::2]
        print('Schedule: ',schedule)
        horario = 'Revisar link'
        description = response.xpath('//div[@class="shortDescription"]//text()').getall()
        description = remove_blank_spaces(' '.join(description))
        image = tools.get_attribute_by_selenium(link,'//figure[@id="productImage"]/img',attr='src')
        
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
        
        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Sala Equis',longitud='404.121.856',latitud='-3.706.093.699.999.990')
        
