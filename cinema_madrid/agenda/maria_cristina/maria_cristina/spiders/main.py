import scrapy 
import urllib
import subprocess
import re
import logging
import time
import datetime as dt

from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, tools
from selenium import webdriver
from requests_html import HTMLSession
session = HTMLSession()


mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

mes_pattern = re.compile(r'de ([a-z]+)')
pattern_year = re.compile(r'\d{4,4}')
pattern_schedule = re.compile(r'(\d+\sd?e?\s?(\w+)?( de \d+)?( al)?( \d+ de \w+ de \d+)?)')
pattern = re.compile(r'sede.*')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

class Webscrape(scrapy.Spider):
    name = 'maria_cristina'
    logger = logging.getLogger(__name__)

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    
    start_urls = ['https://www.fundacioncristinamasaveu.com/centros/sede-fmcmp-madrid/programacion/']


    def parse(self, response, **kwargs):
        schedule_g = response.xpath('//div[@class="w-grid type_grid layout_28484 cols_3"]//article//div[@class="w-vwrapper usg_vwrapper_1 align_left valign_top"]/p[@class="w-post-elm post_custom_field usg_post_custom_field_2 type_text"]//text()').getall()
        general_schedule = []
        for i in schedule_g:
            if re.match(pattern,i.lower()):
                pass
            else:
                general_schedule.append(i.lower().replace('\n','').replace('\r',''))
        comienzo = 0
        final = len(general_schedule)
        step = 2
        box = []
        for i, idx in enumerate(general_schedule):
            if final  != comienzo:

                if general_schedule[comienzo] == 'exposición permanente':
                    result = general_schedule[comienzo]
                    comienzo += 1
                    step += 1
                elif general_schedule[comienzo+1] == 'exposición permanente':
                    result = general_schedule[step]
                    comienzo += 1
                    step += 1
                else:
                    result = ' - '.join(general_schedule[comienzo:step])
                    comienzo += 2
                    step += 2
                box.append(result)
                
            else:
                break

        links = response.xpath('//div[@class="w-grid type_grid layout_28484 cols_3"]//article//div[@class="w-post-elm post_image usg_post_image_1 stretched"]/a/@href').getall()
        images = response.xpath('//div[@class="w-post-elm post_image usg_post_image_1 stretched"]//img/@src').getall()
        for idx, link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                self.logger.info(f'Link {idx}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links), 'image':images[idx],'schedule':box[idx]})
    

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
        

        title = response.xpath('//div[@class="wpb_wrapper"]/h4/span[2]/text()').get()
        schedule = kwargs['schedule']
        description = response.xpath('//div[@class="g-cols wpb_row via_flex valign_top type_default"]//div[@class="wpb_text_column with_show_more_toggle"]/div[@class="wpb_wrapper"]/p[1]//text()').getall()
        description = ' '.join(description)
        category = 'Exposiciones'
        horario = 'Consultar link'

        #Category
        print(schedule)

        #schedule
        if schedule.strip().capitalize() == 'Exposición permanente':
            from_date = 'Exposición permanente'
            to_date = 'Exposición permanente'
        else:
            fp, lp, from_date, to_date = get_schedule.get_schedule(schedule)

        #Image
        image_name = download_images.download_image_with_requests(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Fundacion María Cristina Masaveu Peterson',latitud='40.426.676',longitud='-3.691.599')
    