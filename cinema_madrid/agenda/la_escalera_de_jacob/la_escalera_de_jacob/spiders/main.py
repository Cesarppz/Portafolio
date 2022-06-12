import scrapy 
import urllib
import subprocess
import re
import logging
import time
import datetime as dt

from agenda_tools.get_schedule import remove_blank_spaces
from datetime import datetime
from scrapy_splash import SplashRequest
from agenda_tools import get_schedule, download_images, get_category
from selenium import webdriver
from requests_html import HTMLSession
session = HTMLSession()


mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

mes_pattern = re.compile(r'de ([a-z]+)')
pattern_year = re.compile(r'\d{4,4}')
pattern_schedule = re.compile(r'(\d+\sd?e?\s?(\w+)?( de \d+)?( al)?( \d+ de \w+ de \d+)?)')

base_link = 'https://www.laescaleradejacob.es'

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

class Webscrape(scrapy.Spider):
    name = 'la_escalera_de_jacob'
    logger = logging.getLogger(__name__)

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    
    def start_requests(self):
        start_links = [
            'https://www.laescaleradejacob.es/obras/filtro/formato'
                    ]
        for start_link in start_links:
            yield SplashRequest(start_link,self.parse,cb_kwargs={'start_link':start_link})


    def parse(self, response, **kwargs):
        start_link = kwargs['start_link']
        links = self.get_links_by_scralling(start_link,xpath_expresion='//div[@id="search-list"]//figure/a', attribute='href')
        #links = set(response.xpath('//h2[@class="show-home"]/a/@href').getall()[1:])
        for idx, link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                self.logger.info(f'Link {idx}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})
    

    def get_links_by_scralling(self,url,xpath_expresion, attribute='href'):
        #Instanciar el navegador
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        #chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        driver = webdriver.Firefox(executable_path='../driver/geckodriver', options=options)
        driver.get(url)

        #Get links scralling
        box = []
        previous_heigth = driver.execute_script('return document.body.scrollHeight')
        while True:
            driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
            time.sleep(5)
            new_heigth = driver.execute_script('return document.body.scrollHeight')
            if new_heigth == previous_heigth:
                box.extend(driver.find_elements_by_xpath(xpath_expresion))
                break
            previous_heigth = new_heigth
        box = [i.get_attribute(attribute) for i in box[1:]]
        driver.close()
        return box


    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']        

        title =  response.xpath('//h3[@class="title f-c-r t-upper f-s-14 f-f-tahoma"]/text()').get()

        schedule_link = response.xpath('//div[@class="col-md-12"]/iframe/@src').get().strip()
        response_session = session.get(schedule_link).html
        schedule_days = response_session.xpath('//p[@class="dia_pase_ent"]/span[@class="num_dia"]/text()')
        schedule_months = response_session.xpath('//p[@class="dia_pase_ent"]/span[@class="mes"]/text()')
        schedule = list(zip(schedule_days,schedule_months))

        horario = set(response_session.xpath('//span[@class="time-session"]/text()'))

        description = response.xpath('//div[@class="col-md-12 description"]/p[position()<=3]//text()').getall()
        description = ' '.join(description).strip()

        category = response.xpath('//strong[contains(.,"Género")]/../text()').getall()
        category = get_schedule.remove_blank_spaces(' '.join(category))

        image = response.xpath('//img[@class="img-responsive"]/@src').get()
        #schedule
        schedule_box = []
        for s in schedule:
            schedule_box.append('{} {}'.format(remove_blank_spaces(s[0]), remove_blank_spaces(s[1])))
        print(schedule_box)
        schedule = '{} al {}'.format(schedule_box[0], schedule_box[-1])
        schedule = schedule.replace('Días','').replace('Día','').replace('Del','').replace('del','').replace('Desde','').replace('De','').replace('de','').replace('el','').replace('El','').replace('Hasta','').replace('Sábado','').replace('Lunes','').replace('Martes','').replace('Miércoles','').replace('Jueves','').replace('Viernes','').replace('Domingo','').replace('Aplazado al','').replace('Sepiembre','Septiembre')
        schedule = schedule.replace(' sept ',' sep ')

        print(schedule)
        switch = False
        if 'Hasta' in schedule:
            schedule.replace('Hasta','')
            switch = True
        
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
            fp = '{} {} {}'.format(fp,lp.split()[1], year)
        #Missing year
        elif len(fp.split()) == 2:
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
        
        print(fp)
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

        from_date = from_date.strftime('%d/%m/%Y')
        to_date = to_date.strftime('%d/%m/%Y')

        fp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(fp))
        lp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(lp))
        fp = ' '.join(fp.split()[:2])
        lp = ' '.join(lp.split()[:2])

        #Category
        category = remove_blank_spaces(category)
        print(category)
        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        #image_name = download_images.download(image,idx=idx_for,len_links=len_links, nombre_del_lugar=self.name)
        image = '{}{}'.format(base_link,image)
        image_name = download_images.download_image_with_requests(image,idx=idx, len_links=len_links, nombre_del_lugar=self.name)

        #horarios 
        horario = list(horario)
        print(horario)
        for idx,_ in enumerate(horario):
            print(horario[idx])
            horario[idx] = get_schedule.remove_blank_spaces(horario[idx])
        schedule = list(zip(schedule_box,horario))
        schedule_hour_box = []
        for i in schedule:
            schedule_hour_box.append('{} - {}'.format(i[0],i[-1]))
        horario = ' / '.join((schedule_hour_box))

        yield {
                'From':from_date,
                'To':to_date,
                # 'Desde': fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize().strip(),
                'Place_name/address':'La Escalera de Jacob',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy': 'https://www.casademexico.es/agenda/',
                'Description':description,
                #'Area': 'La Latina ',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'404.113.686',
                'longitud':'-37.028.308',
                'Link':link
                }
    