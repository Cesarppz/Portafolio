import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import logging
import datetime as dt
from agenda_tools import get_category, download_images, months, get_schedule
from datetime import date, datetime
logger = logging.getLogger()

link_image_pattern = re.compile(r'^(http).*/.+\.((jpg|jpeg|png))')
pattern_schedule = re.compile(r'\w+\s\w+\s(\w+\s\w+\s\w+\s\w+\s(\d+)\s\w+\s\w+)')
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_adv = months.dict_of_months_adv_spanish_to_english
patter_link  = re.compile(r'https://www.reservaentradas.com.*')


class Webscrape(scrapy.Spider):
    name = 'conde_duque_santa'
    #allowed_domains = ['www.cinescallao.es']
    start_urls = ['https://cinescondeduque.com/cartelera-conde-duque-santa-engracia/']
    custom_settings=  {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}



    def parse(self, response):
        links = response.xpath('//div[@class="et_pb_section et_pb_section_4 et_section_regular"]//a/@href').getall()
        schedule = response.xpath('//div[@class="et_pb_row et_pb_row_1"]//p/text()').get()
        for idx,link in enumerate(links):
            logger.info(f'Link {idx+1}/{len(links)}')
            if link and not re.match(patter_link,link):
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link': link, 'schedule':schedule, 'idx':idx+1,'len':len(links)})
    

    def new_parse(self, response, **kwargs):
        idx = kwargs['idx']
        len_links = kwargs['len']
        link = kwargs['link']
        schedule = kwargs['schedule']
        title = response.xpath('//div[@class="et_pb_text_inner"]//text()').get()
        #title = response.xpath('//h2[@class="hidden-xs"]/strong/text()').getall()
        image =  response.xpath('//div[@class="et_pb_row et_pb_row_2"]//img/@src').get()
        secon_try_image =  response.xpath('//div[@class="et_pb_row et_pb_row_1"]//img/@src').get()
        description = response.xpath('//div[@class="et_pb_module et_pb_blurb et_pb_blurb_0  et_pb_text_align_left  et_pb_blurb_position_top et_pb_bg_layout_light"]//p/text()').get()

        #Descargar la imagen
        image_name = download_images.download(image,secon_try_image,nombre_del_lugar=self.name,idx=idx,len_links=len_links)

        schedule = schedule.lower().replace('cartelera','')
        fp, lp, from_date, to_date = get_schedule.get_schedule(schedule)
        
        # schedule = schedule.lower()
        # string = re.match(pattern_schedule, schedule).group(1)
        # string = re.split('al',string)
        # fp = string[0].strip().split(' ')
        # lp = string[1].strip().split(' ')
        # fp =  f'{fp[1]} {lp[-1].capitalize()}'
        # lp = f'{lp[1]} {lp[-1].capitalize()}'

        # fp = get_schedule.transform_to_adv(fp)
        # lp = get_schedule.transform_to_adv(lp)

        # from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(fp), year), '%d %b %Y')
        # to_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(lp), year), '%d %b %Y')

        # if from_date.month < mes and to_date.month < mes:
        #     from_date = from_date + dt.timedelta(days=365)
        #     to_date = to_date + dt.timedelta(days=365)
        # elif from_date.month < mes and to_date.month >= mes:
        #     from_date = from_date + dt.timedelta(days=365)
        # elif to_date.month < mes and from_date.month >= mes:
        #     to_date = to_date + dt.timedelta(days=365)
        
        # from_date = from_date.strftime('%d/%m/%Y')
        # to_date = to_date.strftime('%d/%m/%Y')

        # #Titulo completo
        # large_title = f'{title} / Cines Conde Duque Santa Engracia / {fp[1]} {lp[-1].capitalize()} al {lp[1]} {lp[-1].capitalize()}'

        category = 'Cine'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)
        yield {
            'From':from_date,
            'To':to_date,
            # 'Desde': fp ,
            # 'Hasta': lp ,
            'title/Product_name': title.capitalize(),
            'Place_name/address':'Cines Conde Duque Santa Engracia',
            'Categoria' : category,
            'Title_category':main_category,
            'Nº Category': id_category,
            'image':image_name,
            'Hours':schedule.replace('cartelera del ','').capitalize(),
            'Link_to_buy': link,
            'Description':description,
            #'Area': 'Chamberi ',
            'City': 'Madrid',
            'Province': 'Madrid',
            'Country':'España',
            'latitud':'404.426.544',
            'longitud':'-37.018.416',
            'Link':link
        }