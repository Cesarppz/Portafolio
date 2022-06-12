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
pattern = re.compile(r'(^http.*\.\w{3})(.*)')
pattern_url1 = re.compile(r'https://caixaforum.org/es/madrid/familia.*')
pattern_url2 = re.compile(r'https://caixaforum.org/es/madrid/exposiciones.*')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

class Webscrape(scrapy.Spider):
    name = 'caixa_forum_madrid'
    logger = logging.getLogger(__name__)

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    
    def start_requests(self):
        url = ['https://caixaforum.org/es/madrid/exposiciones',
               'https://caixaforum.org/es/madrid/familia']
        for u in url:
            yield SplashRequest(url=u, callback=self.parse , cb_kwargs={'url': u})


    def parse(self, response, **kwargs):
        url = kwargs['url']
        links = response.xpath('//div[@class="croper"]/a/@href').getall()
        #images = response.xpath('//div[@class="w-post-elm post_image usg_post_image_1 stretched"]//img/@src').getall()
        for idx, link in enumerate(links):
            if link:
                self.logger.info(f'Link {idx}/{len(links)}')
                
                #image = re.match(pattern, image).group(1)
                
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'url':url})#, 'image':images[idx]})
        
        next_page = response.xpath('//div[@class="btn btn-viewmore dynamic-color"]/a/@href').get() 
        
        if next_page:
            print('Next page',next_page)
            yield response.follow(next_page, callback=self.parse, cb_kwargs={'url':next_page})
    

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

    def get_attribute_by_selenium(self,url,xpath_expresion,text=True,list_number=0,attr='text'):
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(executable_path='../driver/geckodriver', options=options)
        driver.get(url)
        time.sleep(0.5)
        try:
            driver.find_element_by_xpath('//button[contains(.,"Aceptar todas las Cookies")]').click()
        except Exception:
            pass

        if list_number == 1:
            result = driver.find_elements_by_xpath(xpath_expresion)
            result = ' '.join([i.text for i in result if i != ''])
            driver.close()
            return result
        elif list_number == 0:
            result = driver.find_element_by_xpath(xpath_expresion).get_attribute(attr)
            driver.close()
            return result
        driver.close()

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        url = kwargs['url']
        if re.match(pattern_url1, url):
            category = 'Teatro para Niños'
        else:
            category = 'Exposiciones'

        title = response.xpath('//h1/text()').get()
        schedule = response.xpath('//time/p/text()').get()
        if schedule == None:
            schedule = remove_blank_spaces(response.xpath('//time/text()').get())
        description = response.xpath('//div[@class="introduccion"]/p//text()').getall() + response.xpath('//div[@class="presentacion"]/p//text()').getall()
        description = ' '.join(description)
        if description == '':
            description = response.xpath('//div[@class="secondary-text"]/p[1]//text()').getall()
            description = ' '.join(description)
        image = self.get_attribute_by_selenium(link,'//figure/img',attr='src')
        image = re.match(pattern,image).group(1)
        #image = 'http://localhost:8050/render.html?url={}'.format(image)
        print('Image :',image)
        #category = response.xpath('//div[@class="filters-form-container"]/ul/li[2]//span//text()').get()
        horario = 'Consultar link'

        #Category
        category = get_category.chance_category(category)

        #schedule
        _,_,from_date, to_date = get_schedule.get_schedule(schedule) 
        

        #Image
        title_for_image = '_'.join(remove_blank_spaces(title.lower()).split())
        nombre_del_lugar = '{}_{}'.format(title_for_image,self.name)
        image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=nombre_del_lugar)

        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Caixa Forum Madrid',longitud='40.411.112',latitud='-3.693.571')
    