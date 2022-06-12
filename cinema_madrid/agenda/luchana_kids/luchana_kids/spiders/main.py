import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import logging
from agenda_tools import  get_schedule, download_images, get_category, months
from datetime import datetime
from scrapy.utils.log import configure_logging

configure_logging(install_root_handler=False)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

date = datetime.now()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year  
dict_english_spanish = months.dict_of_months_adv_english_to_spanish
last_day = months.max_days_of_month
base_url = 'https://luchanakids.es'


schedule_pattern = re.compile(r'([a-zA-záéíóú]+\s?y?\s?([a-zA-záéíóú]+)?)\sa\slas.*')
# horario_pattern = re.compile(r'(\w+\sa\slas\s\d+:\d+)')
#horario_patter = re.compile(r'(.*)al(.*)')

class Webscrape(scrapy.Spider):
    name = 'luchana_kids'
    logger = logging.getLogger(name)

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}

    start_urls = ['https://luchanakids.es/']


    def parse(self, response):
        links = set(response.xpath('//div[@class="wld-btn"]/a/@href').getall())
        for idx, link in enumerate(links):
            if link:
                self.logger.info(f'Link {idx+1}/{len(links)}')
                link = '{}{}'.format(base_url,link)
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link,'idx':idx+1,'len':len(links)})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        idx = kwargs['idx']
        len_links = kwargs['len']
        title = response.xpath('//div[@class="inner-wrap"]/h1/text()').get()
        schedule = response.xpath('//div[@class="wpb_wrapper"]//div[@class="wpb_text_column wpb_content_element "]/div[@class="wpb_wrapper"]/p/span/text()').getall()[1:4]
        image = response.xpath('//div[@class="img-with-aniamtion-wrap center"]/div[@class="inner"]/img/@src').get()
        description = response.xpath('//h3[contains(.,"SINOPSIS")]/following-sibling::p/text()').getall()
        description = ''.join(description)
        buy_link = response.xpath('//div[@class="vc_column-inner"]//a[@class="nectar-button large see-through-2  has-icon"]/@href').get()

            #Titulo completo
        horario = []
        box_schedule = []
        print('-'*15)
        print(schedule)
        for i in schedule:
            result_horario = re.search(schedule_pattern,i)
            result_schedule = re.search(schedule_pattern,i)
            if result_horario:
                horario.append(result_horario.group(0))
            if result_schedule:
                box_schedule.append(result_schedule.group(1).capitalize())
        horario = ' y '.join(horario)
        schedule = ' y '.join(box_schedule)
       
        #large_title = get_title.make_title(title,'Luchana kids',fp_schedule=schedule,lp_schedule='')
        image_name = download_images.download_opener(image,nombre_del_lugar='luchana_kids',idx=idx,len_links=len_links)
            #Descargar la imagen
       
        category = 'Niños y Familia'
        category = get_category.chance_category(category)
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
                'Place_name/address':'Teatro Luchana Kids',
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
      
      