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

logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
     #              datefmt='%Y-%m-%d %H:%M')


class Webscrape(scrapy.Spider):
    name = 'fundacion_maphre'
   

    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    
    start_urls = ['https://www.fundacionmapfre.org/arte-y-cultura/exposiciones/']

    def parse(self, response, **kwargs):
        links = response.xpath('//h2/a/@href').getall()
        #images = response.xpath('//div[@class="w-post-elm post_image usg_post_image_1 stretched"]//img/@src').getall()
        for idx, link in enumerate(links):
            if link:
                logger.info(f'Link {idx}/{len(links)}')
                link = 'https://www.fundacionmapfre.org{}'.format(link)
                #image = re.match(pattern, image).group(1)
                
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})#, 'image':images[idx]})
        
    

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

        title = response.xpath('//h1/text()').get()
        schedule = ' - '.join([remove_blank_spaces(i.replace('.',' ')) for i in response.xpath('//h1/following-sibling::p/text()').getall() if remove_blank_spaces(i.replace('.',' ')) != ''])
        description = response.xpath('//div[@class="et_pb_module et_pb_text et_pb_text_10  et_pb_text_align_left et_pb_bg_layout_light"]/div[@class="et_pb_text_inner"]/p[position()<=2]//text()').getall()
        description = ' '.join(description)
        image = response.xpath('//span[@class="et_pb_image_wrap "]/img/@src').get()
        image = 'https://www.fundacionmapfre.org{}'.format(image)
        category = 'Exposiciones'
        horario = 'Consultar link'
        print(schedule)
        #Category
        category = get_category.chance_category(category)

        #schedule
        _,_,from_date, to_date = get_schedule.get_schedule(schedule) 
        

        #Image
        title_for_image = '_'.join(remove_blank_spaces(title.lower()).split())
        nombre_del_lugar = '{}_{}'.format(title_for_image,self.name)
        image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name,title_for_image=nombre_del_lugar )

        yield tools.get_headers(from_date, to_date, title, category, image_name, horario, link, description, place_name='Fundacion Maphre',longitud='404.225.631',latitud='-36.921.871')
    