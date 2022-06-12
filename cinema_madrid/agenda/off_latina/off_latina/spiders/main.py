import scrapy 
import urllib
import subprocess
import re
import logging
import time

from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category
from agenda_tools.get_schedule import remove_blank_spaces
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from requests_html import HTMLSession
import datetime as dt
session = HTMLSession()


logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

mes_pattern = re.compile(r'de ([a-z]+)')
pattern_year = re.compile(r'\d{4,4}')
#pattern_schedule = re.compile(r'\d+ al \d+ de \w+ de \d+')
pattern_schedule = re.compile(r'(\d+\sd?e?\s(\w+)?( de \d+)?( al)?( \d+ de \w+ de \d+)?)')


class Webscrape(scrapy.Spider):
    name = 'off_latina'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    
    def start_requests(self):
        start_links = [
            'https://offlatina.com/programacion/'
                    ]
        for start_link in start_links:
            yield scrapy.Request(start_link,self.parse,cb_kwargs={'start_link':start_link})


    def parse(self, response, **kwargs):
        start_link = kwargs['start_link']
        links = self.get_links_by_scralling(start_link,xpath_expresion='//div[@class="item-holder"]//a')
        image = self.get_links_by_scralling(start_link,xpath_expresion='//div[@class="item-holder"]//img',attribute='src')
        #links = set(response.xpath('//h2[@class="show-home"]/a/@href').getall()[1:])
        for idx, link in enumerate(set(links)):
            logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                logger.info(f'Link {idx}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links), 'image':image[idx]})
    

    def get_links_by_scralling(self,url,xpath_expresion, attribute='href'):
        #Instanciar el navegador
        options = webdriver.ChromeOptions()
        options.add_argument(r'--user-data-dir=/home/cesar/.config/google-chrome/default/Default')
        #options.add_argument("--headless")
        #chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        driver = webdriver.Chrome(executable_path='/home/cesar/Documents/job/web_scraping/javier/agenda/driver/chromedriver', options=options)
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

    
    def get_attribute_selenium(self,url,xpath_expresion,second_xpath_expresion,xpath_expresion_h=None,second_xpath_expresion_h=None,element='schedule'):
        
        options = webdriver.ChromeOptions()
        options.add_argument(r'--user-data-dir=/home/cesar/.config/google-chrome/default/Default')
        # options.add_argument('--profile-directory=Default')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument("--disable-notifications")
        # options.add_argument("disable-infobars")
        #options.add_argument("--headless")
        #chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        driver = webdriver.Chrome(executable_path='/home/cesar/Documents/job/web_scraping/javier/agenda/driver/chromedriver', options=options)
        driver.get(url)
        time.sleep(1.5)
        driver.find_element_by_xpath('//span[contains(.,"Permitir la selección")]').click()
        time.sleep(3) 
        try:
            if element == 'schedule':
                result = driver.find_element_by_xpath(xpath_expresion).text
                if result == '':
                    result = driver.find_element_by_xpath(second_xpath_expresion).text
                print('Result: ',result)
            elif element == 'horario':
                result = driver.find_elements_by_xpath(xpath_expresion)
                result = result[1].text
            elif element == 'schedule/horario':
                result_s = driver.find_element_by_xpath(xpath_expresion).text
                if result_s == '':
                    result_s = driver.find_element_by_xpath(second_xpath_expresion).text

                result_h = driver.find_element_by_xpath(xpath_expresion_h).text
                if result_h == '':
                    result_h = driver.find_element_by_xpath(second_xpath_expresion_h).text

                result = result_s , result_h
            driver.close()
            return result
            
        except NoSuchElementException as ex:
            logger.error('No se encuentra el elemento - Selenium', ex)
            driver.close()
        

    def new_parse(self, response, **kwargs):

        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        image = kwargs['image']
        schedule_link =  response.xpath('//*[contains(text(),"Comprar entradas ")]/@href').get()
        #response_session = session.get('http://localhost:8050/render.html?url={}'.format(schedule_link)).html
        

        title =   response.xpath('//h1/text()').get().capitalize()
        schedule, horario = self.get_attribute_selenium(schedule_link,'//span[@class="session-date ng-binding"]',second_xpath_expresion='//div[@class="medium-4 columns hide-for-small-only"]//span[@class="session-date ng-binding"]',xpath_expresion_h='//p[@class="session-time ng-scope"]/span[@class="ng-binding"]',second_xpath_expresion_h='//div[@class="medium-4 columns hide-for-small-only"]//p[@class="session-time ng-scope"]/span[@class="ng-binding"]',element='schedule/horario')
        description = response.xpath('//div[@class="vc_col-sm-8 vc_col-lg-8 vc_col-xs-1 wpb_column column_container  jupiter-donut- _ jupiter-donut-height-full"][contains(.,"Sinopsis:")]/div[2]//p//text()').getall()
        description = ' '.join(description).strip()
        category = 'Teatro'

        print('Schedule: ', schedule)
        print('horario: ', horario)
        if schedule and horario:
            schedule = schedule.replace('Días','').replace('Día','').replace('Del','').replace('del','').replace('Desde','').replace('De','').replace('de','').replace('el','').replace('El','').replace('Hasta','').replace('Sábado','').replace('Lunes','').replace('Martes','').replace('Miércoles','').replace('Jueves','').replace('Viernes','').replace('Domingo','').replace('Aplazado al','')
    
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
            
            # print(fp)
            # print(lp)
            try:
                fp = get_schedule.transform_to_adv(fp)
                lp = get_schedule.transform_to_adv(lp)
            except Exception:
                pass
            
            # print(fp)
            # print(lp)
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


        else:

            hasta, desde, from_date, to_date = None, None, None, None

        
        #Category   
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        #image_name = download_images.download(image,idx=idx_for,len_links=len_links, nombre_del_lugar=self.name)
        image_name = download_images.download_image_with_requests(image,idx=idx, len_links=len_links, nombre_del_lugar=self.name)
        #Hours
        if type(horario) == list:
            horario = ' - '.join(horario)

        yield {
            'From': from_date,
            'To': to_date,
            'title/Product_name' : title.capitalize().strip(),
            'Place_name/address':'Off Latina',
            'Categoria' : category,
            'Title_category': main_category,
            'Nº Category': id_category,
            'image':image_name,
            'Hours':horario,
            'Link_to_buy': '',
            'Description':description,
            'City': 'Madrid',
            'Province': 'Madrid',
            'Country':'España',
            'latitud':'298.355.294',
            'longitud':'-9.534.232.019.999.990',
            'Link':link
        }

        # yield {
        #         'From':from_date,
        #         'To':to_date,
        #         # 'Desde': desde,
        #         # 'Hasta': hasta,
        #         'title/Product_name': title.capitalize().strip(),
        #         'Place_name/address':'Off Latina',
        #         'Categoria' : category,
        #         'Subcategory': id_category,
		# 		'Title_category': main_category,
        #         'image':image_name,
        #         'Hours':horario, 
        #         'Link_to_buy': 'https://www.casademexico.es/agenda/',
        #         'Description':description,
        #         #'Area': 'La Latina ',
        #         'City': 'Madrid',
        #         'Province': 'Madrid',
        #         'Country':'España',
        #         'latitud':'298.355.294',
        #         'longitud':'-9.534.232.019.999.990',
        #         'Link':link
  #           }