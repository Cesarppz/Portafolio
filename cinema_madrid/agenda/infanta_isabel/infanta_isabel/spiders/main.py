import scrapy 
import re
import logging
from agenda_tools import  get_schedule, download_images, get_category, months
from datetime import datetime
from scrapy.utils.log import configure_logging

configure_logging(install_root_handler=False)
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                   datefmt='%Y-%m-%d %H:%M')

date = datetime.now()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year  
dict_english_spanish = months.dict_of_months_adv_english_to_spanish
last_day = months.max_days_of_month
#base_url = 'https://luchanakids.es'


schedule_pattern = re.compile(r'\d+ de \w+')
horario_pattern = re.compile(r'\d+:\d+')
# horario_pattern = re.compile(r'(\w+\sa\slas\s\d+:\d+)')
#horario_patter = re.compile(r'(.*)al(.*)')

class Webscrape(scrapy.Spider):
    name = 'infanta_isabel'
    logger = logging.getLogger(name)

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}

    start_urls = ['https://www.teatroinfantaisabel.es/espectaculos/en-cartelera/',
                'https://www.teatroinfantaisabel.es/espectaculos/proximamente/']


    def parse(self, response):
        links = set(response.xpath('//div[@class="elementor-widget-container"]//article/a/@href').getall())
        images =  response.xpath('//div[@class="elementor-widget-container"]//article//img/@src').getall()
        assert (len(links) == len(images)), 'no hay la misma cantidad de links y de imagenes'
        print(links)
        for idx, link in enumerate(links):
            if link:
                self.logger.info(f'Link {idx+1}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link,'idx':idx+1,'len':len(links),'image':images[idx]})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        idx = kwargs['idx']
        len_links = kwargs['len']
        image = kwargs['image']

        title = response.xpath('//h1/text()').get().replace(',', '').capitalize()
        schedule = response.xpath('//h2[@class="elementor-icon-box-title"][contains(.," Fecha ")]/following-sibling::p/text()').get().strip().capitalize()
        horario =  response.xpath('//h2[@class="elementor-icon-box-title"]/span[contains(.," Horario ")]/../following-sibling::p/text()').getall()
        description = response.xpath('//div[@class="column"]/p//text()').getall()
        buy_link = link

            #Titulo completo
        
        schedule = re.findall(schedule_pattern,schedule)
        if len(schedule) == 1:
            schedule = get_schedule.remove_blank_spaces(get_schedule.eliminar_de(schedule)[0]).capitalize()
            fp = schedule
            lp = None
            from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(schedule)),year),'%d %b %Y').strftime('%d/%m/%Y')
            to_date = None
        else:
            fp = get_schedule.remove_blank_spaces(get_schedule.eliminar_de(schedule)[0]).capitalize()
            lp = get_schedule.remove_blank_spaces(get_schedule.eliminar_de(schedule)[1]).capitalize()
            from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(fp)),year),'%d %b %Y').strftime('%d/%m/%Y')
            print(schedule)
            print(lp)
            to_date =  datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(lp)),year),'%d %b %Y').strftime('%d/%m/%Y')


        #Image
        image_name = download_images.download_opener(image,nombre_del_lugar=self.name,idx=idx,len_links=len_links)
       
        category = 'Teatro'
        if link == 'https://www.teatroinfantaisabel.es/espectaculos/proximamente/':
            category = 'Niños y Familia'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        #Description
        if description == ['Registrate y recibe las noticias y novedades del Teatro']:
            description = response.xpath('//div[@class="elementor-text-editor elementor-clearfix"]/p//text()').getall()
        description = get_schedule.remove_blank_spaces(' '.join(description))

        #Horario
        horario = [i for i in horario if re.findall(horario_pattern,i)]
        horario = '  /  '.join(horario)


        yield { 'From':from_date,
                'To': to_date,
                # 'Desde':fp,
                # 'Hasta':lp,
                'title/Product_name': title,
                'Place_name/address':'Infanta Isabel',
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
                'latitud':'404.222.447',
                'longitud':'-369.553',
                'Link':link

            }
      
      