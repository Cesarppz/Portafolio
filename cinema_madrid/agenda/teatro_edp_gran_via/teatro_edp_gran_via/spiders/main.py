#encoding=utf-8
import scrapy 
import re
import logging
import datetime as dt
import time

from selenium import webdriver
from scrapy_splash import SplashRequest
from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, months
from agenda_tools.get_schedule import remove_blank_spaces



logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_eng_adv = months.dict_of_months_adv_spanish_to_english 

pattern = re.compile(r'\w+. \w+. \d+')
pattern_schedule = re.compile(r'((\d+,\s)?\d+\sd?e?\s?(\w+.?)?( de \d+)?( al)?( y)?( \d+\s?d?e? \w+.?\,?\s?d?e?\s?(\d+)?)?)')
pattern_extract_images = re.compile(r'\((http.://teatrodelbarrio.com/.*)\)')
#comma_schedule =  re.compile(r'\d+, \d+')
#url_category_pattern = re.compile(r'^https.*/(.*)$')
#base_url = 'https://www.teatroreal.es'


class Webscrape(scrapy.Spider):
    name = 'teatro_edp_gran_via'
    logger = logging.getLogger(name)

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }


    start_urls = [  
                  'https://gruposmedia.com/teatro-edp-gran-via/'
    ]



    def parse(self, response):
        links = set(response.xpath('//div[@class="elementor-column elementor-col-100 elementor-top-column elementor-element elementor-element-5d0174ad"]//article//ul/li//a/@href').getall())

        for idx,link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                # link = '{}{}'.format(base_url,link)
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})
            



    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']


        title =  response.xpath('//h2[@class="elementor-heading-title elementor-size-large"]/text()').get()
        schedule = response.xpath('//span[@class="elementor-icon-list-icon"]/i[@class="fas fa-calendar"]/../../span[@class="elementor-icon-list-text elementor-post-info__item elementor-post-info__item--type-custom"]/text()').get()
        horario = response.xpath('//span[@class="elementor-icon-list-icon"]/i[@class="fas fa-clock"]/../../span[@class="elementor-icon-list-text elementor-post-info__item elementor-post-info__item--type-custom"]/text()').get()
        description = response.xpath('//div[@class="elementor-element elementor-element-611f54ce elementor-widget elementor-widget-text-editor"]/div[@class="elementor-widget-container"]/div[@class="elementor-text-editor elementor-clearfix"]/p[position()<=2]/text()').getall()
        description = get_schedule.remove_blank_spaces(' '.join(description))
        image =  response.xpath('//figure[@class="wp-caption"]/img/@src').get()
        category = response.xpath('//span[@class="elementor-icon-list-icon"]/i[@class="fas fa-tags"]/../../span[@class="elementor-icon-list-text elementor-post-info__item elementor-post-info__item--type-terms"]//text()').getall()
        category = get_schedule.remove_blank_spaces (' '.join(category).split(',')[1])
        
        #Schedule
        
        return_schedule = self.get_dates(schedule)
        fp = return_schedule[0]
        from_date = return_schedule[2]
        lp = return_schedule[1]
        to_date = return_schedule[3]

        #Image
        image_name = download_images.download_image_with_requests(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #description 
        description = get_schedule.remove_blank_spaces(description)

        #Hours
        if horario == '' or horario is None:
            horario = schedule

        horario = horario.split('.')
        horario = '  /  '.join([remove_blank_spaces(i) for i in horario if remove_blank_spaces(i) != ''])

        #category
        category = get_category.chance_category(category)
        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde': fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Teatro EDP Gran Via',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy': link,
                'Description':description,
                #'Area': 'Salamanca ',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'',
                'longitud':'404.224.263',
                'latitud':'-37.088.222',
                'Link':link
                
                }


    def multi_date_schedule(self,schedule):
        schedule = remove_blank_spaces(schedule)
        long_schedule_pattern = re.compile(r'\d+ y \d+ \w+ \d+')
        multi_schedule = re.findall(long_schedule_pattern,schedule)
        if multi_schedule and len(multi_schedule)>=2:
            box = []
            for idx in range(len(multi_schedule)):
                results = self.get_dates(multi_schedule[idx],recursive=True)
                box.append(results)
            
            fp = box[0][0]
            from_date = box[0][2]
            lp = box[-1][1]
            to_date = box[-1][3]

            return [fp, lp, from_date, to_date]
        else:
            return []


    def get_dates(self,schedule,recursive=False):
        print('Schedule : ',schedule)
        schedule = schedule.replace('Días','').replace('Día','').replace('Del','').replace('del','').replace('Desde','').replace('De','').replace('DE','').replace('de','').replace('el','').replace('El','').replace('Hasta','').replace('Sábado','').replace('Lunes','').replace('Martes','').replace('Miércoles','').replace('Jueves','').replace('Viernes','').replace('Domingo','').replace('Aplazado al','').replace('Sepiembre','Septiembre').replace('SOLO','').replace('EL','')
        schedule = schedule.replace(' sept ',' sep ')
        schedule = schedule.strip().capitalize()

        print(schedule)
        switch = False
        schedule = schedule.capitalize()
        if 'Hasta' in schedule:
            schedule = schedule.replace('Hasta','')
            switch = True
        print(schedule)
        if recursive == False:
            schedule_split = self.multi_date_schedule(schedule)
            print(schedule_split)
            if schedule_split == []:
                schedule_split = schedule.split('al')
            else:
                return schedule_split
        else:
            schedule_split = schedule.split('al')
        if len(schedule_split) == 1:
            schedule_split = schedule_split[0].split('-')
        if len(schedule_split) == 1:
            schedule_split = schedule_split[0].split(' y ')
        

        fp , lp = schedule_split[0], schedule_split[-1]
        chanced_year = False

        #Separados por coma
        if ',' in fp:
            fp = fp.split(',')[0]
        if ',' in lp:
            lp = lp.split(',')[-1]
        fp, lp = remove_blank_spaces(fp), remove_blank_spaces(lp)


        #Solo numero 
        if len(fp.split()) == 1:
            if len(lp.split()) == 3:
                year = lp.split()[2]
            fp = '{} {} {}'.format(fp,lp.split()[1], year)
        #Missing year
        elif len(fp.split()) == 2:
            if len(lp.split()) == 3:
                year = lp.split()[2]
            fp = '{} {}'.format(fp,year)
            chanced_year = True
        #lp missing year
        if len(lp.split()) == 2:
            lp = '{} {}'.format(lp,year)
            chanced_year = True
        
        print(fp)
        print(lp)
        try:
            fp = get_schedule.transform_to_adv(fp)
            lp = get_schedule.transform_to_adv(lp)
        except Exception:
            pass
        
        print('fp :',fp)
        print(lp)
        from_date = datetime.strptime(get_schedule.transform_to_adv_spa_eng(fp),'%d %b %Y')
        to_date = datetime.strptime(get_schedule.transform_to_adv_spa_eng(lp),'%d %b %Y')

        if chanced_year:

            if from_date.month < mes and to_date.month < mes:
                from_date = from_date + dt.timedelta(days=365)
                to_date = to_date + dt.timedelta(days=365)

            elif from_date.month < mes and to_date.month >= mes:
                from_date = from_date + dt.timedelta(days=365)

            elif to_date.month < mes and from_date.month >= mes:
                to_date = to_date + dt.timedelta(days=365)

        if switch:
            fp, from_date = None, None
            to_date = to_date.strftime('%d/%m/%Y')

            lp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(lp))
            lp = ' '.join(lp.split()[:2])
        else:

            from_date = from_date.strftime('%d/%m/%Y')
            to_date = to_date.strftime('%d/%m/%Y')

            fp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(fp))
            lp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(lp))
            fp = ' '.join(fp.split()[:2])
            lp = ' '.join(lp.split()[:2])

        return [fp, lp, from_date, to_date]