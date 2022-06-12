#encoding=utf-8
import scrapy 
import re
import logging
import datetime as dt
import time

from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from scrapy_splash import SplashRequest
from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, months



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
# base_url = 'https://www.teatroreal.es'


class Webscrape(scrapy.Spider):
    name = 'teatro_arlequin_gv'
    logger = logging.getLogger(name)

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }


    start_urls = [  
                  'https://teatroarlequingranvia.com/'
    ]



    def parse(self, response):
        links = set(response.xpath('//a[@class="thumb"]/@href').getall())
        # images = response.xpath('//div[@class="page-thumb-artist__block"]/div[@class="page-thumb-artist__block--img"]//picture/img/@src').getall()
        horarios =  response.xpath('//div[@class="box_content"]/p[contains(.,"FUNCIONES")]/text()').getall()
        for idx,link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                #image = '{}{}'.format(base_url,images[idx])
                # link = '{}{}'.format(base_url,link)
                horario = horarios[idx]
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'horario':horario})
            



    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        # image = kwargs['image']


        title =  response.xpath('//h1/text()').get().strip()
        schedule = response.xpath('//div[@class="mec-single-event-date"]//abbr/span/text()').get()
        horario = kwargs['horario']
        description =   response.xpath('//div[@class="wpb_wrapper"]/p/span/text()').getall()
        description = get_schedule.remove_blank_spaces(' '.join(description))
        image =  response.xpath('//div[@class="mec-events-event-image"]/img/@src').get()
        category = response.xpath('//dd[@class="mec-events-event-categories"]/a/text()').get()

        
        #Schedule
        #print('Schedule : ',schedule)
        if 'TEMPORADA' in schedule:
            url = response.xpath('//a[@class="elementor-button-link elementor-button elementor-size-xl"]/@href').get()
            firt_part, last_part = self.get_special_schedule(url) 
            firt_part = datetime.strptime(firt_part, "%d/%m").strftime("%d %b")
            last_part = datetime.strptime(last_part, "%d/%m").strftime("%d %b")
            schedule = '{} al {}'.format(get_schedule.transform_to_adv_eng_spa(firt_part), get_schedule.transform_to_adv_eng_spa(last_part))

        schedule = get_schedule.remove_blank_spaces(schedule.replace('Del','').replace('del','').replace('Desde','').replace('De','').replace('de','').replace('el','').replace('El','').replace('Hasta',''))
        schedule = schedule.replace('sept','sep')
        #print(schedule)
        switch = False
        if 'Hasta' in schedule:
            schedule.replace('Hasta','')
            switch = True
        
        schedule_split = schedule.split('al')
        if len(schedule_split) == 1:
            schedule_split = schedule_split[0].split('-')
        if len(schedule_split) == 1:
            schedule_split = schedule_split[0].split('y')
        

        fp , lp = schedule_split[0], schedule_split[-1]
        chanced_year = False

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


        #Image
        image_name = download_images.download(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #description 
        if description == '' or description == None:
            description = ' '.join([i.strip() for i in  response.xpath('//div[@class="capaDescription"]//text()').getall()])
        description = get_schedule.remove_blank_spaces(description)

        #Hours
        if horario == '' or horario is None:
            horario = schedule
        horario = horario.replace(':','').replace('Abierta contratación giras comunicacion@datasa.es','')
        print(horario)
        
        #horario = ' - '.join(horario.split('.'))

        #category'
        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde': fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Teatro Arlequín Gran Via',
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
                'latitud':'404.211.739',
                'longitud':'-37.082.049',
                'Link':link
                
                }


    def get_special_schedule(self,link):
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        #chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        driver = webdriver.Firefox(executable_path='/home/cesarppz/Documents/jobs/agenda/driver/geckodriver', options=options)
        driver.get(link)
        time.sleep(3)

        box = []
        for i in range(7):
            try:
                cadena = "xdsoft_date xdsoft_day_of_week{} xdsoft_date xdsoft_current xdsoft_weekend".format(i)
                number = int(driver.find_element_by_xpath('//table/tbody/tr/td[@class="{}"]'.format(cadena)).get_attribute('data-date'))
                if number:
                    current_month = int(driver.find_element_by_xpath('//table/tbody/tr/td[@class="{}"]'.format(cadena)).get_attribute('data-month'))
                box.append(number)
            except NoSuchElementException:
                pass
        if box == []:
            for i in range(7):
                try:
                    cadena = "xdsoft_date xdsoft_day_of_week{} xdsoft_date xdsoft_current xdsoft_today".format(i)
                    number = int(driver.find_element_by_xpath('//table/tbody/tr/td[@class="{}"]'.format(cadena)).get_attribute('data-date'))
                    if number:
                        current_month = int(driver.find_element_by_xpath('//table/tbody/tr/td[@class="{}"]'.format(cadena)).get_attribute('data-month'))
                    box.append(number)
                except NoSuchElementException:
                    pass

        current_day = min(box)
        # Ir al ultimo mes
        for _ in range(13):
            driver.find_element_by_xpath('//div[@class="xdsoft_mounthpicker"]/button[@class="xdsoft_next"]').click()
        
        #Tomar los datos de la ultima fecha
        last = []
        for i in range(7):
            try:
                cadena = "xdsoft_date xdsoft_day_of_week{} xdsoft_date xdsoft_weekend".format(i)
                number = int(driver.find_elements_by_xpath('//table/tbody/tr/td[@class="{}"]'.format(cadena))[-1].get_attribute('data-date'))
                if number:
                    last_month = int(driver.find_elements_by_xpath('//table/tbody/tr/td[@class="{}"]'.format(cadena))[-1].get_attribute('data-month'))
                last.append(number)
            except NoSuchElementException:
                pass
            except IndexError:
                pass
        
        last_day = max(last)
        driver.close()

        first_part = '{}/{}'.format(str(current_day), str(current_month + 1))
        last_part = '{}/{}'.format(str(last_day), str(last_month + 1))
        return first_part , last_part