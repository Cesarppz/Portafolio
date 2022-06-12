import scrapy 
import re
import logging
import datetime as dt

from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, months
from agenda_tools.get_schedule import remove_blank_spaces

logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_eng_adv = months.dict_of_months_adv_spanish_to_english 
base_link = 'https://www.wizinkcenter.es/'
pattern = re.compile(r'\w+. \w+. \d+')

class Webscrape(scrapy.Spider):
    name = 'wizink_center'

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    start_urls = [  
                  'https://www.wizinkcenter.es/calendario?categoria=Conciertos'
                  ]


    def parse(self, response):
        links = set( response.xpath('//div[@class="product-thumb"]/header/a/@href').getall())
        for idx,link in enumerate(links):
            logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})


    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        title =   response.xpath('//div[@class="product-page-meta box"]/h3//text()').getall()
        description = response.xpath('//div[@class="row row-wrap"]/div[@class="col-md-12"]/p/text()').get()
        image = response.xpath('//div[@class="col-md-8"]//img/@src').get()
        category = 'Música'
        apertura =  response.xpath('//span[@class="product-page-meta-title"][contains(.,"Apertura")]/following-sibling::span/text()').get().replace('.','')
        inicio = response.xpath('//span[@class="product-page-meta-title"][contains(.,"Inicio")]/following-sibling::span/text()').get().replace('.','')
        cierre =  response.xpath('//span[@class="product-page-meta-title"][contains(.,"Fin")]/following-sibling::span/text()').get().replace('.','')
        
        #title 
        title = ' '.join([i.strip() for i in title])

        #Schedule
        main_schedule_month = response.xpath('//div[@class="col-lg-1"]/div[@class="row "]/div[@class="col-lg-12 hidden-xs"]/text()').get()
        main_schedule_number = response.xpath('//div[@class="col-lg-1"]/div[@class="row mb20"]/div[@class="col-xs-12 col-lg-12"]/text()').get()
        schedule_month =  response.xpath('//div[@class="col-lg-1"]/div[@class="row"][position()=1]/div[@class="col-lg-12"]/text()').getall()
        schedule_number = response.xpath('//div[@class="col-lg-1"]/div[@class="row"][position()=3]/div[@class="col-lg-12"]/text()').getall()
        pass_schedule = False
        if schedule_number and schedule_month:

            if main_schedule_number and main_schedule_month:
                main_schedule_number =[main_schedule_number]
                main_schedule_month = [main_schedule_month]

                main_schedule_number.extend(schedule_number)
                main_schedule_month.extend(schedule_month)
                
                schedule_number = main_schedule_number
                schedule_month = main_schedule_month

            fp, lp = ' '.join([remove_blank_spaces(schedule_number[0]),remove_blank_spaces(schedule_month[0])]).capitalize(), ' '.join([remove_blank_spaces(schedule_number[-1]),remove_blank_spaces(schedule_month[-1])]).capitalize()
            pass_schedule = True #Interruptor para decir que ya tengo los schedules
            
            print('\t AQUI')

        if pass_schedule == False:
            fp  = ' '.join([remove_blank_spaces(main_schedule_number),remove_blank_spaces(main_schedule_month)]).capitalize()
            lp = fp


        print('Schedule: ',schedule_month,schedule_number)
        
        print(fp,lp)
        from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(fp), year), '%d %b %Y')
        to_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(lp), year), '%d %b %Y')
        

        if from_date.month < mes and to_date.month < mes:
            from_date = from_date + dt.timedelta(days=365)
            to_date = to_date + dt.timedelta(days=365)
        elif from_date.month < mes and to_date.month >= mes:
            from_date = from_date + dt.timedelta(days=365)
        elif to_date.month < mes and from_date.month >= mes:
            to_date = to_date + dt.timedelta(days=365)
        

        from_date = from_date.strftime('%d/%m/%Y')
        to_date = to_date.strftime('%d/%m/%Y')

        #Hours
        horario = 'Apertura: {}  /  Inicio: {}'.format(apertura,inicio)

        #Image
        image_name = download_images.download(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #description 
        if description == '\xa0':
            description = response.xpath('//div[@class="row row-wrap"]/div[@class="col-md-12"]/p//text()').getall()
            description = ' '.join(description).replace('\xa0','').replace('  ',' ').strip()
        #category  
        category = get_category.chance_category(category)       
        id_category = get_category.id_category(category)
        main_category = get_category.main_category(category)

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde': fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Wizink Center',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy': '{}{}'.format(base_link,link),
                'Description':description,
                #'Area': 'Salamanca ',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'4.042.387.859.999.990',
                'longitud':'-36.717.512',
                'Link':'{}{}'.format(base_link,link)
                
                }
