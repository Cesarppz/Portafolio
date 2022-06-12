import scrapy 
import urllib
import subprocess
import re
import logging
from datetime import datetime
import datetime as dt
from agenda_tools import get_title, get_schedule, download_images, get_category, months
logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_eng_adv = months.dict_of_months_adv_spanish_to_english 

pattern_schedule = re.compile(r'(\d+\s+de\s+\w+)')
base_link = 'https://www.teatrocircoprice.es'


class Webscrape(scrapy.Spider):
    name = 'circo_price'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    start_urls = [  
                  'https://www.teatrocircoprice.es/programacion'
                  ]


    def parse(self, response):
        box_div = response.xpath('//div[@class="views-row"]')
        links = box_div.xpath('//div[@class="field field-name-field-outstanding-image"]/a/@href').getall()
        links = ['{}{}'.format(base_link,i) for i in links]
        image_link = box_div.xpath('//div[@class="field field-name-field-outstanding-image"]/a/img/@src').getall()
        image_link = ['{}{}'.format(base_link,i) for i in image_link]
        for idx, (link,image) in enumerate(zip(links,image_link)):
            logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links), 'image':image})

        next_page = response.xpath('//*[@class="pager__item pager__item--next"]//a/@href').get()
        if next_page:
            print(next_page)
            next_page = '{}{}{}'.format(base_link,'/programacion',response.xpath('//*[@class="pager__item pager__item--next"]//a/@href').get())
            yield response.follow(next_page, callback=self.parse)

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        image = kwargs['image']

        title =  response.xpath('//h1/text()').get().replace('\n','').strip()
        schedule = response.xpath('//div[@class="group-dates"]/div//text()').getall() 
        description = response.xpath('//*[@class="field field-name-field-entradilla"]/p/text()').get()
        horario1 = response.xpath('//div[@class="field field-name-field-entradilla"]/p[contains(.,"Calendario Circo de Cerca:")]/following-sibling::ul//text()').getall() 
        category = response.xpath('//div[@class="field field-name-field-tags"]/span/text()').get()
        schedule = ''.join(schedule).replace(' ','').strip().replace('\n',' ')
        print(link)
        schedule = schedule.replace('Sólo','').replace('Hasta','').replace('Desde','').strip()
        
        schedule = schedule.split('  ')
        print(schedule)
        if len(schedule) > 2:
            fp , lp = schedule[0], schedule[-1]

            fp_date = fp.strip().split()[-1]
            lp_date = lp.strip().split()[-1]
            
            fp_date = dict_spa_eng_adv[fp_date]
            lp_date = dict_spa_eng_adv[lp_date]
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
        else:
            fp = schedule[0]
            lp = fp 
            fp_date = fp.strip().split()[-1]
            
            fp_date = dict_spa_eng_adv[fp_date]
            from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(fp), year), '%d %b %Y')

            if from_date.month < mes:
                from_date = from_date + dt.timedelta(days=365)
            
            from_date = from_date.strftime('%d/%m/%Y')
            to_date = from_date
        
        #Hours
        if horario1:
            horario = ''.join(horario1).replace('\n\t',' - ')
        else:
            horario =  response.xpath('//*[@class="field field-name-field-schedule-txt"]/p/text()').getall()
            horario = ' - '.join(horario).replace('\n',' ')
        # horario = ''.join(horario).replace('\xa0','')
        #Image
        image_name = download_images.download(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #category 
        if category:
            category = category.replace('\n','').replace('  ',' ').strip().capitalize()
        else:
            category = 'Conciertos'
        print(category)
        if category == 'Circo':
            category = 'Magia y Circo'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde':f'Desde {fp}',
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Circo Price',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy':  link,
                'Description':description,
                #'Area': 'Lavapiés',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'40.405.985',
                'longitud':'-3.698.592',
                'Link':link
                
                }
