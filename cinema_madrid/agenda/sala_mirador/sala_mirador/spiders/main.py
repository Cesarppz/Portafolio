#encoding=utf-8
#from agenda.teatro_del_barrio.teatro_del_barrio.settings import ROBOTSTXT_OBEY
import scrapy 
import re
import logging
import datetime as dt
import time

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
base_url = 'https://lamirador.com/'


class Webscrape(scrapy.Spider):
    name = 'sala_mirador'
    logger = logging.getLogger(name)

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    start_urls = [  
                  'https://lamirador.com/proximas-funciones' 
                  ]

    def get_schedule_selenium(self,url):
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        #chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        driver = webdriver.Firefox(executable_path='../driver/geckodriver', options=options)
        driver.get(url)

        #Click al cartel
        time.sleep(3)
        driver.find_element_by_xpath('//input[@id="fecha_seleccionada"]').click()
        #Extraer los dias
        days = driver.find_elements_by_xpath('//td[@class="day"]')
        days = [i.text for i in days]
        #Extraer el mes y el year
        month_and_year = driver.find_element_by_xpath('//th[@class="datepicker-switch"]').text

        box = []
        for i in days:
            box.append('{} {}'.format(i,month_and_year))
        
        return box


    def parse(self, response):
        links = set(response.xpath('//div[@class="img_list"]/a/@href').getall())
        images = response.xpath('//div[@class="img_list"]/a/img/@src').getall()

        for idx,link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                image = '{}{}'.format(base_url,images[idx])
                link = '{}{}'.format(base_url,link)
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'image':image})
            
        next_page = response.xpath('//ul[@class="pagination"]/li[last()]/a/@href').get()

        yield response.follow(next_page,callback=self.parse)


    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        image = kwargs['image']

        title =  response.xpath('//h1/text()').get().strip()
        schedule =  self.get_schedule_selenium(link)
        horario = response.xpath('//td[contains(.,"Horario")]/following-sibling::td/p/text()').get()
        description =  response.xpath('//div[@class="col-md-9"]/div//text()').getall()
        description = get_schedule.remove_blank_spaces(' '.join(description))

        
        #Schedule
        schedule = '{} al {}'.format(schedule[0],schedule[-1])
        print('Schedule : ',schedule)
        schedule = schedule.replace('Del','').replace('del','').replace('Desde','').replace('De','').replace('de','').replace('el','').replace('El','').replace('Hasta','')
        
        if ',' in schedule:
            schedule = schedule.split(',')[1]
        schedule = get_schedule.remove_blank_spaces(schedule)
        print(schedule)
        switch = False
        if 'Hasta' in schedule:
            schedule.replace('Hasta','')
            switch = True
        
        schedule_split = schedule.split('al')
        if len(schedule_split) == 1:
            schedule_split = schedule_split[0].split('y')
        if len(schedule_split) == 1:
            schedule_split = schedule_split[0].split('-')

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

            if from_date.month < mes and to_date.month < mes :
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

        print(fp)
        print(lp)
        fp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(fp))
        lp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(lp))
        fp = ' '.join(fp.split()[:2])
        lp = ' '.join(lp.split()[:2])


        #Image
        image_name = download_images.download_image_with_requests(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #description 
        if description == '' or description == None:
            description = ' '.join([i.strip() for i in  response.xpath('//div[@class="capaDescription"]//text()').getall()])
        description = get_schedule.remove_blank_spaces(description)

        #Hours
        if horario == '' or horario is None:
            horario = schedule

        if type(horario) == list:
            horario = '  /  '.join(horario)
        #category
        category = 'Teatro'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde': fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Sala Mirador',
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
                'latitud':'4.040.704.240.000.000',
                'longitud':'-36.988.561',
                'Link':link
                
                }
