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
from requests_html import HTMLSession
session = HTMLSession()



logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_eng_adv = months.dict_of_months_adv_spanish_to_english 

pattern = re.compile(r'\w+. \w+. \d+')
pattern_schedule = re.compile(r'((\d+,\s)?\d+\sd?e?\s?(\w+.?)?( de \d+)?( al)?( y)?( \d+\s?d?e? \w+.?\,?\s?d?e?\s?(\d+)?)?)')
pattern_extract_images = re.compile(r'\((http.://teatrodelbarrio.com/.*)\)')
#comma_schedule =  re.compile(r'\d+, \d+')
#url_category_pattern = re.compile(r'^https.*/(.*)$')
#base_url = 'https://www.teatroreal.es'


class Webscrape(scrapy.Spider):
    name = 'sala_azarte'
    logger = logging.getLogger(name)

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    def start_requests(self):
        url = 'https://azarte.com/sala-de-teatro/'

        yield SplashRequest(url=url, callback=self.parse )



    def parse(self, response):
        main_link = response.request.url
        links = set( response.xpath('//ul[@class="products"]/li/a/@href').getall())
        print('Links : ',links)

        for idx,link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                # link = '{}{}'.format(base_url,link)
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'main_link':main_link})
            



    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        main_link = kwargs['main_link']
        response_session = session.get('http://localhost:8050/render.html?url={}'.format(link)).html

        title =  response.xpath('//div[@class="product-title-wrapper sm-display-none display-block"]//text()').get()
        schedule = response.xpath('//div[@class="short-description"]/p/strong/text()').get().split('a las')[0]
        if len(response.xpath('//div[@class="short-description"]/p/strong/text()').get().split('a las')) > 1:
            horario =  response.xpath('//div[@class="short-description"]/p/strong/text()').get().split('a las')[1]
        else:
            horario = 'Revisar link'
        description = response.xpath('//div[@class="short-description"]/p[contains(.,"Sinopsis")]/following-sibling::p/em/text()').getall()
        description = get_schedule.remove_blank_spaces(' '.join(description))
        image = response.xpath('//div[@class="item woocommerce-product-gallery__image"]//img[@class="wp-post-image"]/@src').get()
        category = 'Teatro'

        
        #Schedule
        if schedule and horario != 'Revisar link':
            print('Schedule : ',schedule)
            schedule = schedule.replace('Del','').replace('Días','').replace('del','').replace('Desde','').replace('De','').replace('de','').replace('el','').replace('El','').replace('Hasta','')
            schedule = schedule.replace('sept','sep')
            print(schedule)
            switch = False
            if 'Hasta' in schedule:
                schedule.replace('Hasta','')
                switch = True
            
            schedule_split = schedule.split('al')
            if len(schedule_split) == 1:
                schedule_split = schedule_split[0].split('-')
            if len(schedule_split) == 1:
                schedule_split = schedule_split[0].split(' y ')
            

            fp , lp = schedule_split[0], schedule_split[-1]
            chanced_year = False

            #Separados por coma
            if ',' in fp:
                fp = fp.split(',')[0]
            if ',' in lp:
                lp = lp.split(',')[-1]
            fp, lp = remove_blank_spaces(fp), remove_blank_spaces(lp)
            #Solo numero 
            if len(fp.split()) == 1:
                fp = '{} {} {}'.format(fp,lp.split()[1], year)
            #Missing year
            elif len(fp.split()) == 2:
                fp = '{} {}'.format(fp,year)
                chanced_year = True
            #lp missing year
            if len(lp.split()) == 2:
                lp = '{} {}'.format(lp,year)
                chanced_year = True
            
            print(fp)
            print(lp)
            try:
                fp = get_schedule.transform_to_adv(fp)
                lp = get_schedule.transform_to_adv(lp)
            except Exception:
                pass
            
            print(fp)
            print(lp)
            try:
                from_date = datetime.strptime(get_schedule.transform_to_adv_spa_eng(fp),'%d %b %Y')
                to_date = datetime.strptime(get_schedule.transform_to_adv_spa_eng(lp),'%d %b %Y')

                if chanced_year:

                    if from_date.month < mes and to_date.month < mes:
                        from_date = from_date + dt.timedelta(days=365)
                        to_date = to_date + dt.timedelta(days=365)

                    elif from_date.month < mes and to_date.month >= mes:
                        from_date = from_date + dt.timedelta(days=365)

                    elif to_date.month < mes and from_date.month >= mes:
                        to_date = to_date + dt.timedelta(days=365)

                if switch:
                    fp, from_date = None, None

                from_date = from_date.strftime('%d/%m/%Y')
                to_date = to_date.strftime('%d/%m/%Y')

                fp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(fp))
                lp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(lp))
                fp = ' '.join(fp.split()[:2])
                lp = ' '.join(lp.split()[:2])

            except:
                from_date, to_date = 'Revisar link', 'Revisar link'

        else:
            from_date, to_date = 'Revisar link', 'Revisar link'

        
        #Image
        image_name = download_images.download(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #description 
        if description == '' or description == None:
            description = ' '.join([i.strip() for i in  response.xpath('//div[@class="capaDescription"]//text()').getall()])
        description = get_schedule.remove_blank_spaces(description)

        #Hours
        if horario is None or horario == []:
            horario = schedule

        #category
        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)
        main_category = get_category.main_category(category)

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde': fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Sala Azarte',
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
                'latitud':'4.042.141.669.999.990',
                'longitud':'-36.983.519',
                'Link':link
                
                }
