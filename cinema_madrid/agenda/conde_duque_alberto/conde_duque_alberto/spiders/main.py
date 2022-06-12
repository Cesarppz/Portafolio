import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import logging
from datetime import datetime
from agenda_tools import get_category, download_images, months, get_schedule

logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
link_image_pattern = re.compile(r'^(http).*/.+\.((jpg|jpeg|png))')
pattern_schedule = re.compile(r'\w+\s\w+\s(\w+\s\w+\s\w+\s\w+\s(\d+)\s\w+\s\w+)')
patter_link  = re.compile(r'https://www.reservaentradas.com.*')

class Webscrape(scrapy.Spider):
    name = 'conde_duque_alberto'
    #allowed_domains = ['www.cinescallao.es']
    start_urls = ['https://cinescondeduque.com/cartelera-conde-duque-verdi-alberto-aguilera/']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}


    def parse(self, response):
        original_links = response.xpath('//div[@id="CarteleraAA"]//a/@href').getall()
        schedule = response.xpath('//div[@class="et_pb_row et_pb_row_1"]//p/text()').get()
        for idx, link in enumerate(original_links):
            if link and not re.match(patter_link,link):
                logger.info(f'Link {idx+1}/{len(original_links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link': link, 'schedule':schedule, 'idx':idx+1, 'len':len(original_links)})
    

    def new_parse(self, response, **kwargs):
        idx = kwargs['idx']
        len_links = kwargs['len']
        link = kwargs['link']
        schedule = kwargs['schedule']
        title = response.xpath('//div[@class="et_pb_text_inner"]//text()').get()
        image =   response.xpath('//div[@class="box-shadow-overlay"]/../img/@src').get()   #response.xpath('//div[@class="et_pb_row et_pb_row_2"]//img/@src').get()
        secon_try_image =  response.xpath('//div[@class="et_pb_row et_pb_row_1"]//img/@src').get()
        print('Schedule', schedule)
        description = response.xpath('//div[@class="et_pb_module et_pb_blurb et_pb_blurb_0  et_pb_text_align_left  et_pb_blurb_position_top et_pb_bg_layout_light"]//p/text()').get()
        second_try_description = response.xpath('//div[@class="su-note-inner su-u-clearfix su-u-trim"]/p/text()').get()
        #Descargar la imagen
        image_name = download_images.download(image, secon_try_image, nombre_del_lugar=self.name,idx=idx,len_links=len_links)


        schedule = schedule.lower().replace('cartelera','')
        fp, lp, from_date, to_date = get_schedule.get_schedule(schedule)
        print('Schedule', schedule)
        # string = re.match(pattern_schedule, schedule).group(1)
        # string = re.split('al',string)
        # fp = string[0].strip().split(' ')
        # lp = string[1].strip().split(' ')
        # fp =  f'{fp[1]} {lp[-1].capitalize()}'
        # lp = f'{lp[1]} {lp[-1].capitalize()}'
        # fp = get_schedule.transform_to_adv(fp)
        # lp = get_schedule.transform_to_adv(lp)
        # from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(fp), year), '%d %b %Y').strftime('%d/%m/%Y')
        # to_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(lp), year), '%d %b %Y').strftime('%d/%m/%Y')

        category = 'Cine'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        if description == None:
            description = second_try_description

        
        yield {
            'From':from_date,
            'To':to_date,
            # 'Desde': fp ,
            # 'Hasta': lp ,
            'title/Product_name': title.capitalize(),
            'Place_name/address':'Cines Conde Duque Alberto Aguilera',
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
            'latitud':'404.299.926',
            'longitud':'-3.706.534.999.999.990',
            'Link':link
        }