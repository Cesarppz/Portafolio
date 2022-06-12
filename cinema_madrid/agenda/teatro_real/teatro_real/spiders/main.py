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
pattern_name_images = re.compile(r'https://.*/(.*)#.*')
#comma_schedule =  re.compile(r'\d+, \d+')
#url_category_pattern = re.compile(r'^https.*/(.*)$')
base_url = 'https://www.teatroreal.es'


class Webscrape(scrapy.Spider):
    name = 'teatro_real'
    logger = logging.getLogger(name)

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }


    start_urls = [  
                  'https://www.teatroreal.es/es/temporada-21-22/opera#toContent',
                  'https://www.teatroreal.es/es/temporada-21-22/danza#toContent',
                  'https://www.teatroreal.es/es/temporada-21-22/conciertos-y-recitales#toContent',
                  'https://www.teatroreal.es/es/temporada-21-22/flamenco-real#toContent',
                  'https://www.teatroreal.es/es/temporada-21-22/real-junior#toContent',
                  'https://www.teatroreal.es/es/temporada-21-22/otras-actividades#toContent'
    ]



    def parse(self, response):
        main_link = response.request.url
        links = set( response.xpath('//div[@class="page-thumb-artist__block"]/p/a/@href').getall())
        images = response.xpath('//div[@class="page-thumb-artist__block"]/div[@class="page-thumb-artist__block--img"]//picture/img/@src').getall()

        for idx,link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                image = '{}{}'.format(base_url,images[idx])
                # link = '{}{}'.format(base_url,link)
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'image':image,'main_link':main_link})
            



    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        image = kwargs['image']
        main_link = kwargs['main_link']
        #response_session = session.get('http://localhost:8050/render.html?url={}'.format(link)).html

        title =  response.xpath('//h1/text()').get().strip()
        schedule = response.xpath('//div[@class="wrap-content-hero"]/h3/text()').getall()[-1]
        horario =  zip(response.xpath('//div[@class="functions-show__block--item-date"]/p/text()').getall() ,  response.xpath('//div[@class="functions-show__block--item-hour"]/p/text()').getall())
        description =   response.xpath('//div[@class="wrap-text-free collapsible-mobile"]/p[position()<=2]//text()').getall()
        description = get_schedule.remove_blank_spaces(' '.join(description))

        
        #Schedule
        print('Schedule : ',schedule)
        schedule = get_schedule.remove_blank_spaces(schedule.replace('Del','').replace('del','').replace('Desde','').replace('De','').replace('de','').replace('el','').replace('El','').replace('Hasta',''))
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
            schedule_split = schedule_split[0].split('y')
        

        fp , lp = schedule_split[0], schedule_split[-1]
        chanced_year = False

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
        from_date = datetime.strptime(get_schedule.transform_to_adv_spa_eng(fp),'%d %b %y')
        to_date = datetime.strptime(get_schedule.transform_to_adv_spa_eng(lp),'%d %b %y')

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


        #Image
        sub_name = re.match(pattern_name_images,main_link).group(1)
        image_name = download_images.download(image,idx='{}_{}'.format(sub_name,idx),len_links=len_links, nombre_del_lugar=self.name)

        #description 
        if description == '' or description == None:
            description = ' '.join([i.strip() for i in  response.xpath('//div[@class="capaDescription"]//text()').getall()])
        description = get_schedule.remove_blank_spaces(description)

        #Hours
        if horario is None or horario == []:
            horario = schedule
        else:
            horario = '  /  '.join(['{} - {}'.format(i,j) for (i,j) in horario])
            print(horario)

        #category
        if main_link == 'https://www.teatroreal.es/es/temporada-21-22/opera#toContent':
            category = 'ópera'
        elif main_link == 'https://www.teatroreal.es/es/temporada-21-22/danza#toContent':
            category = 'Danza'
        elif main_link == 'https://www.teatroreal.es/es/temporada-21-22/conciertos-y-recitales#toContent':
            category = 'Música'
        elif main_link == 'https://www.teatroreal.es/es/temporada-21-22/flamenco-real#toContent':
            category = 'Flamenco'
        elif main_link == 'https://www.teatroreal.es/es/temporada-21-22/real-junior#toContent':
            category = 'Niños y Familia'
        elif main_link == 'https://www.teatroreal.es/es/temporada-21-22/otras-actividades#toContent':
            category = 'Performance'
        

        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde': fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Teatro Real',
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
                'latitud':'40.418.299',
                'longitud':'-3.710.578',
                'Link':link
                
                }
