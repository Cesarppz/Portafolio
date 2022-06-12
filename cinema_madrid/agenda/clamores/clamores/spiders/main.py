import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import logging 
from agenda_tools import get_schedule,download_images,get_category
from datetime import datetime
import datetime as dt
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
logger = logging.getLogger()


link_image_pattern = re.compile(r'^(https?).*/(.+\.(jpg|jpeg|png))')
patter_links = re.compile(r'^(http).*//.*\/((exposiciones|cine-en-casa-de-mexico|literatura|familias|teatro))/.*')
horario_patter = re.compile(r'(.*)al(.*)')
pattern_schedule = re.compile(r'\d+\s\w+')


class Webscrape(scrapy.Spider):
    name = 'clamores'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}

    start_urls = ['https://dice.fm/bundles/sala-clamores-42ba'
                  ]


    def parse(self, response):
        links = set( response.xpath('//div[@class="EventParts__EventBlock-sc-12dip7s-9 kOxLNf"]//a/@href').getall())
        for idx, link in enumerate(links):
            if link:
                logger.info(f'Link {idx+1}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link,'idx':idx+1,'len':len(links)})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        idx = kwargs['idx']
        len_links = kwargs['len']
        title = response.xpath('//h1/text()').get()
        schedule = response.xpath('//div[@class="EventDetailsTitle__Date-sc-16azpgd-2 cxIkJm"]/text()').get()
        #horario = None
        image = response.xpath('//div[@class="EventDetailsImage__Container-sc-1dv87kv-0 cCnugi"]/img/@src').get()
        description = response.xpath('//div/h2[contains(.,"About")]/following-sibling::div//p/text()').get()
        #description = ''.join(description)
            #buy_link = response.xpath('//p[@class="texto"]//a/@href').get()

        if schedule:
            desde = re.findall(pattern_schedule,schedule)[0].replace(',','')
        else:
            desde = None
        #Descargar la imagen
        image_name = download_images.download(image,nombre_del_lugar=self.name,idx=idx,len_links=len_links)
        
        category = 'Jazz y Soul'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        #Schedule
        from_date = datetime.strptime('{} {}'.format(desde,year),'%d %b %Y')
        if from_date.month < mes:
            from_date = from_date + dt.timedelta(days=365)
        from_date = from_date.strftime('%d/%m/%Y')
        desde = get_schedule.transform_to_adv_eng_spa(desde)

        #Horario
        horario = schedule.split(',')[-1].replace('CET','').replace('CEST','').strip()
    

        yield { 'From':from_date,
                'To':from_date,
                # 'Desde':desde,
                # 'Hasta':desde,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Sala Clamores',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy': link, 
                'Description':description,
                #'Area': 'Chamberi ',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'40.431.118',
                'longitud':'-37.009.577',
                'Link':link
            }
      