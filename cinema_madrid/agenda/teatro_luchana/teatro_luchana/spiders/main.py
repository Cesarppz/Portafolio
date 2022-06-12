import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
from agenda_tools import download_images,get_schedule,get_title, get_category, months
import logging
logger = logging.getLogger()
from datetime import datetime
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

link_image_pattern = re.compile(r'^(https?).*/(.+\.(jpg|jpeg|png))')
patter_links = re.compile(r'^(http).*//.*\/((exposiciones|cine-en-casa-de-mexico|literatura|familias|teatro))/.*')
horario_patter = re.compile(r'(.*)al(.*)')

date = datetime.now()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_english_spanish = months.dict_of_months_adv_english_to_spanish
last_day = months.max_days_of_month

base_link = 'https://teatrosluchana.es'

class Webscrape(scrapy.Spider):
    name = 'teatro_luchana'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}
    start_urls = ['https://teatrosluchana.es/']


    def parse(self, response):
        links = set(response.xpath('//a[contains(.,"Entradas")]/@href').getall())
        for idx , link in enumerate(links):
            if link:
                if link.startswith('/'):
                    link = '{}{}'.format(base_link,link)
                logger.info(f'Link {idx+1}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link,'idx':idx+1,'len':len(links)})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        title = response.xpath('//div[@class="col span_6 section-title no-date"]//h1/text()').get()
        schedule =  response.xpath('//div[@class="wpb_text_column wpb_content_element "]/div[@class="wpb_wrapper" and contains(.,"HORARIO")]/p/span/text()').getall()
        #horario = None
        image = response.xpath('//div[@class="wpb_wrapper"]//img/@src').get()
        description = response.xpath('//div[(@class="wpb_wrapper")and(position()=1)]/p/text()').get()
        #description = ''.join(description)
        buy_link = response.xpath('//div[@class="vc_column-inner"]/div[@class="wpb_wrapper"]/a[@class="nectar-button large see-through-2  has-icon"]/@href').get()

        horario = None
        if len(schedule) == 1:
            schedule = schedule[0]
        else:
            schedule = ' '.join(schedule).replace('\n','')

        if schedule:
            horario = schedule
            schedule = get_schedule.eliminar_de_not_list(schedule,replace_pattern='a las')
            schedule = schedule.split()

            fp, lp = schedule[0], schedule[1]
        else:
            schedule = None
            fp , lp = None , None 
        #Titulo completo
        large_title = get_title.make_title(title,'Teatro luchana',fp_schedule=fp, lp_schedule=fp)


            #Descargar la imagen
        image_name = download_images.download(image,nombre_del_lugar='teatro_luchana',idx=idx,len_links=len_links)

        category = 'Teatro'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        mes_fecha = date.strftime('%b').capitalize()
        max_day = last_day[mes_fecha]
        from_date = datetime.strptime('1 {} {}'.format(mes_fecha,year),'%d %b %Y').strftime('%d/%m/%Y')
        to_date = datetime.strptime('{} {} {}'.format(max_day,mes_fecha,year),'%d %b %Y').strftime('%d/%m/%Y')
        mes_fecha = dict_english_spanish[mes_fecha]


        yield { 'From':from_date,
                'To': to_date,
                # 'Desde':'1 {}'.format(mes_fecha),
                # 'Hasta':'{} {}'.format(max_day,mes_fecha),
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Teatro Luchana',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy': buy_link,
                'Description':description,
                #'Area': 'Chamberi ',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'404.318.718',
                'longitud':'-36.982.594',
                'Link':link

            }
      