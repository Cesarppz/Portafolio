from agenda_tools import get_schedule
import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import logging
from agenda_tools.get_schedule import eliminar_spacios_list
from agenda_tools import get_title, download_images, get_category
from datetime import date, datetime

link_image_pattern = re.compile(r'^(http).*/(.+\.(jpg|jpeg))')
horario_pattern = re.compile(r'((\w+\s\d+/\d+)|(\d+:\d+))')
logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

class Webscrape(scrapy.Spider):
    name = 'cinescallao'
    #allowed_domains = ['www.cinescallao.es']
    #custom_settings= {}
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}

    start_urls = ['http://www.cinescallao.es']


    def parse(self, response):
        dirty_links1 = response.xpath('//div[@class="et_pb_row et_pb_row_0 et_pb_equal_columns et_pb_gutters2"]//a/@href').getall()
        dirty_links2 =  response.xpath('//div[@class="et_pb_row et_pb_row_2 et_pb_equal_columns et_pb_gutters2"]//a/@href').getall()
        dirty_links3 =  response.xpath('//div[@class="et_pb_module et_pb_image et_pb_image_0"]/a/@href').getall()
        dirty_links = dirty_links1 + dirty_links2 
        buy_links = dirty_links[1::2]
        links = dirty_links[::2]
        if len(links) % 2 != 0:
            links.append(dirty_links[-1])
        print(links)

        if buy_links and links:
            for idx , (link,buy) in enumerate(zip(links,buy_links)):
                print(link)
                if link:
                    logger.info(f'Link {idx+1}/{len(links)}')
                    yield response.follow(link, callback=self.new_parse,cb_kwargs={'link':link,'buy_link':buy,'idx':idx+1,'len':len(links)})
        else:
            for idx , (link,buy) in enumerate(zip(dirty_links3,dirty_links3)):
                print(link)
                if link:
                    logger.info(f'Link {idx+1}/{len(links)}')
                    yield response.follow(link, callback=self.new_parse,cb_kwargs={'link':link,'buy_link':buy,'idx':idx+1,'len':len(links)})
    

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        idx = kwargs['idx']
        len_links = kwargs['len']
        buy_link = kwargs['buy_link']
        title = response.xpath('//h1/text()').get()
        schedule = response.xpath('//ul/li/text()').getall()
        horario = response.xpath('//ul/li/strong/text()').getall()
        second_try_horario = response.xpath('//div[@class="et_pb_text_inner"]/p//text()').getall()
        image = response.xpath('//div[@class="et_pb_section et_pb_section_1 et_pb_with_background et_section_regular"]//img/@src').get()
        description = response.xpath('//div[@class="et_pb_module et_pb_text et_pb_text_4  et_pb_text_align_left et_pb_bg_layout_light"]/div[@class="et_pb_text_inner"]/p/text()').get()        #Extraer el horario

        
        #eliminar espacios 
        schedule = eliminar_spacios_list(schedule)
        for i in range(len(schedule)):
            schedule[i].strip()

        schedule_date = list(zip(schedule, horario))
        result_schedule = []
        for fecha, hora in schedule_date:
            result_schedule.append(fecha+' - '+hora)
        result_schedule = '  /  '.join(result_schedule)
        
        if horario == []:
            result_schedule = []
            for i in second_try_horario:
                result = re.search(horario_pattern,i)
                if result and result.string.strip() not in result_schedule:
                    result_schedule.append(result.string.strip())
            result_schedule = ' '.join(result_schedule)
            result_schedule = '  /  '.join(result_schedule.split(','))

        
        #print(schedule)
        #Titulo completo
        if schedule:
            fp = schedule[0].strip().split(' ')[-1]
            lp = schedule[-1].strip().split(' ')[-1]
            from_date = '{}/{}'.format(fp,year)
            to_date = '{}/{}'.format(lp,year)
            fp = datetime.strptime(from_date,'%d/%m/%Y').strftime('%d %b')
            lp = datetime.strptime(to_date,'%d/%m/%Y').strftime('%d %b')
            fp = get_schedule.transform_to_adv_eng_spa(fp)
            lp = get_schedule.transform_to_adv_eng_spa(lp)
            #print(fp)
        else :
            fp , lp, from_date, to_date = None, None, None, None

        #Descargar la imagen
        try:
            image_name = download_images.download(image,nombre_del_lugar=self.name,idx=idx,len_links=len_links)
        except:
            image_name = download_images.download_image_with_requests(image,nombre_del_lugar=self.name,idx=idx,len_links=len_links)
        
        category = 'Cine'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)
        yield {
            'From':from_date,
            'To':to_date,
            # 'Desde':fp,
            # 'Hasta': lp,
            'title/Product_name': title.capitalize(),
            'Place_name/address':'Cines Callao',
            'Categoria' : category,
            'Title_category':main_category,
            'Nº Category': id_category,
            'image':image_name,
            'Hours':result_schedule,
            'Link_to_buy': buy_link,
            'Description':description,
            #'Area': 'Chamberi ',
            'City': 'Madrid',
            'Province': 'Madrid',
            'Country':'España',
            'latitud':'404.199.807',
            'longitud':'-3.706.086',
            'Link':link
        }