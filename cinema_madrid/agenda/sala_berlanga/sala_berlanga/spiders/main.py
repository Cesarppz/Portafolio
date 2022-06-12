import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import logging
from datetime import datetime
from agenda_tools import get_category, download_images, get_schedule
logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

link_image_pattern = re.compile(r'^(http).*/.+\.((jpg|jpeg|png))')
horario_patter = re.compile(r'(.*)al(.*)')
pattern_schedule = re.compile(r'(\d+\s?d?e?\s?\w* al \d+ de \w+)')
pattern_schedule2 = re.compile(r'\d*,?\s?\d+ y \d+ de \w+')

class Webscrape(scrapy.Spider):
    name = 'sala_berlanga'
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}
    #allowed_domains = ['www.cinescallao.es']

    start_urls = ['http://www.salaberlanga.com/category/cartelera/']


    def parse(self, response):
        links = response.xpath('//div[@class="post-group"]//div[@class="thumbnail"]/a/@href').getall()
        for idx, link in enumerate(links):
            if link:
                logger.info(f'Link {idx+1}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'Link': link, 'idx':idx+1, 'len':len(links)})
    
    def elinate_spaces(self, x):
        for _ in x:
            try:
                x.remove('\n')
            except ValueError:
                break
    def new_parse(self, response, **kwargs):
        link = kwargs['Link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        title = response.xpath('//h1/text()').get()
        schedule = response.xpath('//p/*[contains(.,"PROGRAMACIÓN")]/ancestor::p/text()').getall()
        second_try_schedule =  response.xpath('//p/*[contains(.,"PROGRAMACIÓN")]/../following-sibling::p[1]/text()').getall()
        horario = response.xpath('//p[(@class="texto") and (position()>=3) and (position()<=18)]//text()').getall()
        image = response.xpath('//div[@class="content"]//img/@src').get()
        description = response.xpath('//p[preceding::p[starts-with(.,"Acerca de  ")]]//text()').getall()
        buy_link = response.xpath('//p[@class="texto"]//a/@href').get()
        #Extraer el horario
        print('-'*20)
        if schedule:
            for i in schedule:
                calendario = re.findall(pattern_schedule,i)
                if calendario:
                    break

            if calendario:
                calendario = calendario[0].split('al')
                fp = calendario[0].strip()
                lp = calendario[-1].strip()
                if len(fp) <= 2:
                    lp = lp.split(' ')
                    desde = f'{fp} {lp[-1]}'
                    hasta = f'{lp[0]} {lp[-1]}'
                else:
                    desde = fp
                if type(lp) == list:
                    hasta =  f'{lp[0]} {lp[-1]}'
                else :
                    hasta = lp
            else :
                for i in schedule:
                    calendario = re.findall(pattern_schedule2,i)
                    if calendario:
                        break
                if calendario:
                    calendario = calendario[0].split('y')
                    desde = calendario[0].strip()[:2]
                    hasta = calendario[-1].strip()
                    if len(desde) <= 2:
                        print('-'*20)
                        hasta = hasta.split(' ')
                        desde = f'{desde} {hasta[-1]}'
                        hasta = f'{hasta[0]} {hasta[-1]}'
                else:
                    desde = None
                    hasta = None

        elif second_try_schedule:
            for i in second_try_schedule:
                calendario = re.findall(pattern_schedule,i)
                if calendario:
                    break

            if calendario:
                calendario = calendario[0].split('al')
                fp = calendario[0].strip()
                lp = calendario[-1].strip()
                if len(fp) <= 2:
                    lp = lp.split(' ')
                    desde = f'{fp} {lp[-1]}'
                    hasta = f'{lp[0]} {lp[-1]}'
                else:
                    desde = fp
                if type(lp) == list:
                    hasta =  f'{lp[0]} {lp[-1]}'
                else :
                    hasta = lp
            else :
                for i in second_try_schedule:
                    calendario = re.findall(pattern_schedule2,i)
                    if calendario:
                        break
                if calendario:
                    calendario = calendario[0].split('y')
                    desde = calendario[0].strip()[:2]
                    hasta = calendario[-1].strip()
                    if len(desde) <= 2:
                        print('-'*20)
                        hasta = hasta.split(' ')
                        desde = f'{desde} {hasta[-1]}'
                        hasta = f'{hasta[0]} {hasta[-1]}'

                else:
                    desde = None
                    hasta = None

        else:
            desde = None
            hasta = None
        # Convertir las fechas en abrevacion y crear las columnas from, to
        if desde and hasta != None:
            fp = desde.replace('de','').replace('  ',' ').strip()
            lp = hasta.replace('de','').replace('  ',' ').strip()
            try:
                fp = get_schedule.transform_to_adv(fp)
                lp = get_schedule.transform_to_adv(lp)
                from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(fp), year), '%d %b %Y').strftime('%d/%m/%Y')
                to_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(lp), year), '%d %b %Y').strftime('%d/%m/%Y')
            except:
                from_date, to_date = None, None
        else :
            from_date, to_date = None, None

        image_name = download_images.download(image, nombre_del_lugar='sala_berlanga',idx=idx,len_links=len_links)


        category = 'Cine de Autor'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield {
            'From':from_date,
            'To':to_date,
            # 'Desde':fp,
            # 'Hasta': lp,
            'title/Product_name': title.capitalize(),
            'Place_name/address':'Sala Berlanga',
            'Categoria' : category,
            'Title_category':main_category,
            'Nº Category': id_category,
            'image':image_name,
            'Hours':None,
            'Link_to_buy': buy_link,
            'Description':description,
            #'Area': 'Chamberi ',
            'City': 'Madrid',
            'Province': 'Madrid',
            'Country':'España',
            'latitud':'4.043.592.719.999.990',
            'longitud':'-37.144.398',
            'Link':link
            }
