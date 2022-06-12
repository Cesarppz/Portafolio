import scrapy 
import urllib
import subprocess
import re
import logging
import time
import datetime as dt

from datetime import datetime
from scrapy_splash import SplashRequest
from agenda_tools import get_schedule, download_images, get_category, tools
from agenda_tools.get_schedule import remove_blank_spaces
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
    name = 'fundacion_juan_march'
    logger = logging.getLogger(__name__)

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    
    def start_requests(self):
        url = 'https://www.march.es/es/madrid'

        yield SplashRequest(url=url, callback=self.parse )


    def parse(self, response, **kwargs):
        links = response.xpath('//div[@class="c-snippet__top-container flex-grow-1 mb-3 mb-lg-5 u-relative d-flex flex-column"]/a[@class="c-snippet__img w-100-mobile mb-4 u-relative "]/@href').getall()
        images = response.xpath('//div[@class="c-snippet__top-container flex-grow-1 mb-3 mb-lg-5 u-relative d-flex flex-column"]/a[@class="c-snippet__img w-100-mobile mb-4 u-relative "]/img/@src').getall()
        for idx, link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                self.logger.info(f'Link {idx}/{len(links)}')
                link = 'https://www.march.es{}'.format(link)
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'image':images[idx]})
    

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

        title = remove_blank_spaces(response.xpath('//h1[@class="c-titular-segundo-nivel js-reduce-text-size"]/text()').get())
        schedule_g = response.xpath('//a[@id="dropdownMenuLinks"]/span/text()').get().split(',')
        schedule = schedule_g[0]
        description = response.xpath('//div[@class="u-column-2 u-column-gap-6"]//text()').getall()
        description = remove_blank_spaces(' '.join(description))
        category = remove_blank_spaces(response.xpath('//div[@class="c-hero-bg-image__texto-lateral"]/span/text()').get())
        horario = schedule_g[1]
        image = kwargs['image']

        #Category
        if category.lower() == 'concierto':
            category = 'Clásica'
        category = get_category.chance_category(category)

        #schedule
        if schedule.strip().capitalize() == 'Exposición permanente':
            from_date = 'Exposición permanente'
            to_date = 'Exposición permanente'
        else:
            fp, lp, from_date, to_date = get_schedule.get_schedule(schedule)

        #Image
        image_name = download_images.download_image_with_requests(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Fundacion Juan March',longitud='',latitud='')
    