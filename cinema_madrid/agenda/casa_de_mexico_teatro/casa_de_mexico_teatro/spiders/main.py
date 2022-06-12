import logging
import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import datetime as dt
from datetime import datetime
import logging
from agenda_tools import get_category,get_schedule,get_title,download_images, months

logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

pattern_schedule = re.compile(r'\d+\s+de\s+\w+')
pattern_horario = re.compile(r'([A-Za-záéíóú]+ \d+ de [A-Za-záéíóú]+)( y \d+ de [A-Za-záéíóú]+)?( a las \d+:\d+)?')


class Webscrape(scrapy.Spider):
    name = 'casa_de_mexico_teatro'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}
    start_urls = [
                  'https://www.casademexico.es/teatro/'
                  ]


    def parse(self, response):
        links = set( response.xpath('//div[@class="row proximamente"]//a/@href').getall())
        for idx , link in enumerate(links):
            if link:
                logger.info(f'Link {idx+1}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link,'idx':idx+1,'len':len(links)})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title = response.xpath('//div[@class="col-sm-9 col-12"]/h1/text()').get()
        schedule = response.xpath('//div[@class="col-sm-9 col-12"]//div[@class="fecha"]/text()').getall()
        image = response.xpath('//div[@class="carousel-inner"]//picture//source[last()]/@srcset').getall()[-1]
        description = response.xpath('//div[@class="info-descripcion"]//p//text()').getall()
        description = ' '.join(description)
        category = response.xpath('//div[@class="etiquetas"]/h3/text()').get().capitalize()
        horario = response.xpath('//div[@class="info-descripcion"]//p//span//text()').getall()
        second_try_horario = response.xpath('//div[@class="info-descripcion"]//text()').getall()
        horario = ' '.join(horario).replace('\xa0',' ').replace('  ',' ').lower()
        second_try_horario = ' '.join(second_try_horario).replace('\xa0',' ').replace('  ',' ').lower()

        schedule = get_schedule.schedule_in_list(schedule,pattern_schedule)
        for idx , i in enumerate(schedule):
            i = i.replace('de',' ')
            schedule[idx] = ' '.join(i.split())

            #Titulo completo
        #large_title = get_title.make_title(title,'Casa de Mexico',fp_schedule=schedule[0].strip(),lp_schedule=schedule[1].strip())

            #Descargar la imagen
        image_name = download_images.download(image,nombre_del_lugar='casa_de_mexico_teatro',idx=idx,len_links=len_links)

            #category
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        #Hourss
        if horario:
            list_horario = re.findall(pattern_horario,horario)
            #print(list_horario)
            clean_horario = []
            for h in list_horario:
                h = ' '.join(h).replace('  ',' ').strip()
                clean_horario.append(h)
            if clean_horario == []:
                clean_horario = schedule
            clean_horario = ' / '.join(clean_horario)
            
        elif second_try_horario:
            list_horario = re.findall(pattern_horario,second_try_horario)
            #print(list_horario)
            clean_horario = []
            for h in list_horario:
                h = ' '.join(h)
                clean_horario.append(h)
            if clean_horario == []:
                clean_horario = schedule
            clean_horario = ' - '.join(clean_horario)
        else :
            horario = schedule

        #Schedule 
        fp = schedule[0].replace('  ','').strip()
        lp = schedule[0].replace('  ','').strip()
        fp = get_schedule.transform_to_adv(fp)
        lp = get_schedule.transform_to_adv(lp)

        from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(fp), year), '%d %b %Y')
        to_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(lp), year), '%d %b %Y')


        if to_date.month < mes:
            to_date = to_date + dt.timedelta(days=365)

        from_date = from_date.strftime('%d/%m/%Y')
        to_date = to_date.strftime('%d/%m/%Y')

        yield {
                'From':from_date,
                'To': to_date,
                #'Desde': fp,
                #'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Casa de Mexico',
                'Categoria' : category,
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

