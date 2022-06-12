import scrapy 
import urllib
import subprocess
import re
import logging
import time
import datetime as dt

from datetime import datetime
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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

class Webscrape(scrapy.Spider):
    name = 'teatro_lara'
    logger = logging.getLogger(__name__)

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    
    def start_requests(self):
        start_links = [
            'https://entradas.teatrolara.com/entradas.teatrolara/es_ES/tickets?_ga=2.2565488.1924042174.1633015321-470052594.1633015321'
                    ]
        for start_link in start_links:
            yield scrapy.Request(start_link,self.parse,cb_kwargs={'start_link':start_link})


    def parse(self, response, **kwargs):
        start_link = kwargs['start_link']
        links = self.get_links_by_scralling(start_link,xpath_expresion='//div[@class="small-12 columns flex-growing-elem"]//a', attribute='href')
        image = self.get_links_by_scralling(start_link,xpath_expresion='//div[@class="small-12 columns flex-growing-elem"]//a/img[@class="ng-scope"]',attribute='lazy-img')
        #links = set(response.xpath('//h2[@class="show-home"]/a/@href').getall()[1:])
        for idx, link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                self.logger.info(f'Link {idx}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links), 'image':image[idx]})
    

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

    def get_attribute_by_selenium(self,url,xpath_expresion,text=True,list_number=0):
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(executable_path='../driver/geckodriver', options=options)
        driver.get(url)
        time.sleep(0.5)

        if list_number == 1:
            result = driver.find_elements_by_xpath(xpath_expresion)
            result = ' '.join([i.text for i in result if i != ''])
            driver.close()
            return result
        elif list_number == 0:
            result = driver.find_elements_by_xpath(xpath_expresion)[0].text
            driver.close()
            return result

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        image = kwargs['image']
        response_session = session.get('http://localhost:8050/render.html?url={}'.format(link)).html
        

        title = response_session.xpath('//h1/text()')
        if title:
            title = title[0].capitalize()

        schedule = response_session.xpath('//span[@class="session-date ng-binding"]/text()')
        if schedule:
            schedule = schedule[0]
        if schedule == []:
            schedule =  self.get_attribute_by_selenium(link,'//span[@class="icon fi-clock"]/following-sibling::span[@class="session-date ng-binding"]/text()',list_number=1)
            print('Selenium')
        print('Schedule :',schedule)
        
        horario =  response_session.xpath('//p[@class="session-time ng-scope"]//span[@class="ng-binding"]/text()')
        if horario:
            horario = horario[0]
        if horario == []:
            horario = response_session.xpath('//span[@class="icon fi-clock"]/following-sibling::span[@class="session-date ng-binding"]/text()')

        description = response_session.xpath('//div[@class="ng-binding collapsed"]/p//text()')
        description = ' '.join(description).strip()
        category = 'Teatro'

        #schedule
        print('-'*25)
        print(schedule)
        schedule = re.findall(pattern_schedule,schedule)[0][0]
        schedule = get_schedule.remove_blank_spaces(schedule.replace('de','')).split('al')
        
        if len(schedule) < 2:
            fp, lp = get_schedule.remove_blank_spaces(schedule[0]), get_schedule.remove_blank_spaces(schedule[0])
        else:
            fp, lp = get_schedule.remove_blank_spaces(schedule[0]), get_schedule.remove_blank_spaces(schedule[1])
        # if len(schedule[0].split()) <= 2:
        #     fp, lp = schedule[0], schedule[1]
        # else:
        #     fp, lp = get_schedule.remove_blank_spaces(schedule[0]), get_schedule.remove_blank_spaces(schedule[1])
        print('fp ',fp)

        if len(fp) <= 2:
            fp = '{} {} {}'.format(fp, lp.split()[1], lp.split()[-1])
        elif len(fp.split()) == 2:
            fp = '{} {}'.format(fp, lp.split()[-1])
        print('fp ',fp)

        fp, lp = get_schedule.remove_blank_spaces(fp), get_schedule.remove_blank_spaces(lp)
        desde = ' '.join(fp.split()[:-1])
        hasta = ' '.join(lp.split()[:-1])
        fp_date = get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(fp))
        from_date = datetime.strptime(fp_date,'%d %b %Y')
        lp_date = get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(lp))
        to_date = datetime.strptime(lp_date,'%d %b %Y')

        if from_date.month < mes and to_date.month < mes:
            from_date = from_date + dt.timedelta(days=365)
            to_date = to_date + dt.timedelta(days=365)
        elif from_date.month < mes and to_date.month >= mes:
            from_date = from_date + dt.timedelta(days=365)
        elif to_date.month < mes and from_date.month >= mes:
            to_date = to_date + dt.timedelta(days=365)

        from_date = from_date.strftime('%d/%m/%Y')
        to_date = to_date.strftime('%d/%m/%Y')

        #Category
        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)
        main_category = get_category.main_category(category)

        #image_name = download_images.download(image,idx=idx_for,len_links=len_links, nombre_del_lugar=self.name)
        image_name = download_images.download_image_with_requests(image,idx=idx, len_links=len_links, nombre_del_lugar=self.name)

        #Title
        if title == []:
            title = self.get_attribute_by_selenium(link,'//h1',list_number=0)
        title = title.capitalize().strip()

        yield {
                'From':from_date,
                'To':to_date,
                # 'Desde': desde,
                # 'Hasta': hasta,
                'title/Product_name': title,
                'Place_name/address':'Teatro Lara',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy': link,
                'Description':description,
                #'Area': 'La Latina ',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'404.221.091',
                'longitud':'-3.704.466.799.999.990',  
                'Link':link
                
                }
    