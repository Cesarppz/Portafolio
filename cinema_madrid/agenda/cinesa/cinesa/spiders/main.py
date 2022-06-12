#encoding=utf-8
import scrapy 
import re
import logging
import datetime as dt
import time

from selenium import webdriver
from scrapy_splash import SplashRequest
from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, months
from agenda_tools.get_schedule import remove_blank_spaces



logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_eng_adv = months.dict_of_months_adv_spanish_to_english 



class Webscrape(scrapy.Spider):
    name = 'cinesa'
    logger = logging.getLogger(name)

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }


    start_urls = [  
                  'https://www.cinesa.es/Peliculas/Cartelera'
    ]



    def parse(self, response):
        links = set(response.xpath('//li[@class=@class="listado-peliculas-item"]/a[@class="vf linkcartel"]/@href').getall())

        for idx,link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                # link = '{}{}'.format(base_url,link)
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})
            



    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']


        title =  response.xpath('//div[@id="center"]/text()').get().strip()
        schedule = 'Consultar link'
        horario = 'Consultar link'
        description = response.xpath('//article[@class="descripcion d1 cuadros_ficha"]/p[contains(.,"Sinopsis: ")]/text()').getall()[:3]
        description = get_schedule.remove_blank_spaces(' '.join(description))
        image =  response.xpath('//article[@id="cartel"]/img[@class="cartel"]/@src').get()
        category = 'Cine'
        
        #Schedule
        
        #Image
        image_name = download_images.download_image_with_requests(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #description 
        description = get_schedule.remove_blank_spaces(description)

        #Hours
        if horario == '' or horario is None:
            horario = schedule

        # horario = horario.split('.')
        # horario = '  /  '.join([remove_blank_spaces(i) for i in horario if remove_blank_spaces(i) != ''])

        #category

        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield { 
                'From':'Consultar link',
                'To':'Consultar link',
                # 'Desde': fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Cinesa',
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
                'latitud':'355.416.714',
                'longitud':'-1.116.862.672',
                'Link':link
                
                }