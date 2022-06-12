import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import logging
import datetime as dt
from datetime import datetime
from agenda_tools import get_title, get_schedule, download_images, get_category
logger = logging.getLogger()

mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

link_image_pattern = re.compile(r'^(https?).*/(.+\.(jpg|jpeg|png))')
patter_links = re.compile(r'^(http).*//.*\/((exposiciones|cine-en-casa-de-mexico|literatura|familias|teatro))/.*')
pattern_schedule = re.compile(r'\d+\s+de\s+\w+')
#pattern_horario = re.compile(r'(([A-Za-záéíóú]+ )?\d+( de [A-Za-záéíóú]+)?)( y \d+ de [A-Za-záéíóú]+)?( a las \d+:\d+)?')
pattern_horario = re.compile(r'([A-Za-záéíóú]+ \d+ de [A-Za-záéíóú]+)( y \d+ de [A-Za-záéíóú]+)?( a las \d+:\d+)?')


class Webscrape(scrapy.Spider):
    name = 'casa_de_mexico'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    start_urls = [  
                  'https://www.casademexico.es/cine-en-casa-de-mexico/',
                  'https://www.casademexico.es/literatura/', 
                  'https://www.casademexico.es/familias/',
                  ]


    def parse(self, response):
        links = set( response.xpath('//div[@class="row proximamente"]//a/@href').getall())
        for idx, link in enumerate(links):
            logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title = response.xpath('//h1/text()').get()
        schedule = response.xpath('//div[@class="fecha"]/text()').getall()
        image = response.xpath('//div[@class="col-12"]//source/@srcset').getall()[-1]
        description =  response.xpath('//div[@class="info-descripcion"]/p[1]//text()').getall()
        description = ''.join(description).strip().replace('\n',' ').replace('\xa0',' ')
        category = response.xpath('//div[@class="etiquetas"]/h3/text()').get()
        horario = response.xpath('//div[@class="info-descripcion"]//p//span//text()').getall()
        second_try_horario = response.xpath('//div[@class="info-descripcion"]//text()').getall()
        horario = ' '.join(horario).replace('\xa0',' ').replace('  ',' ').lower()
        second_try_horario = ' '.join(second_try_horario).replace('\xa0',' ').replace('  ',' ').lower()

        schedule = [schedule[0], schedule[1]]
        schedule_list = get_schedule.schedule_in_list(schedule,pattern_schedule)
        schedule_list = get_schedule.eliminar_de(schedule_list)
        #Image
        len_links = f'{len_links}_{category}'
        image_name = download_images.download(image,idx=idx,len_links=len_links, nombre_del_lugar='casa_de_mexico')
        #Category

        if category == 'Cine':
            category = 'Cine de Autor'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)
        

        # print(horario)
        if horario:
            list_horario = re.findall(pattern_horario,horario)
            #print(list_horario)
            clean_horario = []
            for h in list_horario:
                h = ' '.join(h).replace('  ',' ').strip()
                clean_horario.append(h)
            if clean_horario == []:
                clean_horario = schedule
            clean_horario = ' / '.join(clean_horario).replace('  ',' ').strip()
            
        elif second_try_horario:
            list_horario = re.findall(pattern_horario,second_try_horario)
            #print(list_horario)
            clean_horario = []
            for h in list_horario:
                h = ' '.join(h)
                clean_horario.append(h)
            if clean_horario == []:
                clean_horario = schedule
            clean_horario = ' - '.join(clean_horario).replace('  ',' ').strip()
        else :
            horario = schedule

        #Schedule 
        fp = schedule_list[0].replace('de','').replace('  ',' ').strip().replace('  ',' ')
        lp = schedule_list[1].replace('de','').replace('  ',' ').strip().replace('  ',' ')
        fp = get_schedule.transform_to_adv(fp)
        lp = get_schedule.transform_to_adv(lp)

        from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(fp), year), '%d %b %Y')
        to_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(lp), year), '%d %b %Y')

        if to_date.month < mes:
            to_date = to_date + dt.timedelta(days=365)

        from_date = from_date.strftime('%d/%m/%Y')
        to_date = to_date.strftime('%d/%m/%Y')
        print(fp)
        print(lp)


        yield {
                'From':from_date,
                'To':to_date,
                #'Desde': fp,
                #'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Casa de Mexico',
                'Categoria': category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,                    
                'Hours':clean_horario,
                'Link_to_buy': 'https://www.casademexico.es/agenda/',
                'Description':description,
                #'Area': 'Chamberi ',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'360.921.669',
                'longitud':'-958.873.978',
                'Link':link
                
                }
