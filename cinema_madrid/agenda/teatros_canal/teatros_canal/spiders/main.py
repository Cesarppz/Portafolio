import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import logging
from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category
from selenium import webdriver
import time

logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

link_image_pattern = re.compile(r'^(https?).*/(.+\.(jpg|jpeg|png))')
patter_links = re.compile(r'^(http).*//.*\/(([\-\w]+)-?(s)?)')
pattern_schedule = re.compile(r'\d+\,?[\,\d\w\s]+ de [a-z]+')
pattern_schedule2 = re.compile(r'\d+ de [a-z]+')
mes_pattern = re.compile(r'de ([a-z]+)')
pattern_year = re.compile(r'\d{4,4}')

class Webscrape(scrapy.Spider):
    name = 'teatros_canal'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    
    def start_requests(self):
        start_links = [
            'https://www.teatroscanal.com/entradas/teatro-madrid/',
            'https://www.teatroscanal.com/entradas/danza-madrid/',
            'https://www.teatroscanal.com/entradas/conciertos-madrid/',
            'https://www.teatroscanal.com/entradas/opera-madrid/',
            'https://www.teatroscanal.com/entradas/teatro-infantil-madrid/',
            'https://www.teatroscanal.com/entradas/flamenco-madrid/',
            'https://www.teatroscanal.com/teatro-comedia-humor-madrid/',
            'https://www.teatroscanal.com/entradas/cultura-urbana/',
            'https://www.teatroscanal.com/entradas/circo-madrid/' 
                    ]
        for start_link in start_links:
            category = re.match(patter_links,start_link).group(3)
            yield scrapy.Request(start_link,self.parse,cb_kwargs={'category':category,'start_link':start_link})

    def parse(self, response, **kwargs):
        category = kwargs['category']
        start_link = kwargs['start_link']
        links = self.get_links_by_scralling(start_link)
        #links = set(response.xpath('//h2[@class="show-home"]/a/@href').getall()[1:])
        for idx, link in enumerate(links):
            logger.info(f'Link {idx+1}/{len(links)} / {category}')
            if link:
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'category':category})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx_for = kwargs['idx']
        
        title =  response.xpath('//h1/text()').get()
        schedule =  response.xpath('//div[@class="fecha-show-show2"]/p/text()').get()
        horario = response.xpath('//ul[@id="toggle-view"]/li/h3[contains(.,"Fechas y Horarios                        ")]/following-sibling::div[@class="panel"]/table/tbody//p/text()').getall()
        image = response.xpath('//div[@class="destacado-right"]/p/img/@src').get()
        description =  response.xpath('//div[@id="tabs1-info"]/p[position()<6]//text()').getall()
        description = ''.join(description).strip()
        category = kwargs['category']

        print('-'*25)
        print(schedule)
        try:
            schedule = re.findall(pattern_schedule,schedule)[0]
            schedule_result = schedule.split('al')
            if schedule == schedule_result[0]:
                schedule_result = schedule.split(' y')
        except IndexError:
            schedule_result = re.findall(pattern_schedule2,schedule)[0]
        print(schedule_result)

        if len(schedule_result[0]) <= 2 and type(schedule_result)==list:
            for i in schedule_result:
                mes = re.findall(mes_pattern,i)
                if mes:
                    schedule_result[0] = '{} {}'.format(schedule_result[0],mes[0])
                    break

        elif len(schedule_result[0]) >=3 and len(schedule_result[0]) < 7 or re.findall(mes_pattern,schedule_result[0]) == []:
            for i in schedule_result:
                mes = re.findall(mes_pattern,i)
                if mes:
                    schedule_result[0] = '{} {}'.format(schedule_result[0].split(',')[0],mes[0])
                    break

        if type(schedule_result)==list:
            for idx, i in enumerate(schedule_result):
                schedule_result[idx] = i.replace('de','').strip()
            fp = schedule_result[0]
            lp = schedule_result[-1].replace('el ','')
        else:
            schedule_result = schedule_result.replace('de','').strip()
            fp = schedule_result
            lp = schedule_result

        desde = get_schedule.transform_to_adv(fp)
        hasta = get_schedule.transform_to_adv(lp)
        
        #Image
        image_name = download_images.download(image,idx=idx_for,len_links=len_links, nombre_del_lugar=self.name)

        # Category
        category = category.capitalize()
        category = category.replace('-madrid','').replace('-','')

        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)
        main_category = get_category.main_category(category)
        
        #Years datetime
        years = re.findall(pattern_year,schedule)
        fp = get_schedule.get_datetime(fp)
        lp = get_schedule.get_datetime(lp)
        if years == []:
            from_date = f'{fp} {year}'.replace('  ',' ').strip()[:11]
            to_date = f'{lp} {year}'.replace('  ',' ').strip()[:11]

            from_date = datetime.strptime(from_date,'%d %b %Y').strftime('%d/%m/%Y')
            to_date = datetime.strptime(to_date,'%d %b %Y').strftime('%d/%m/%Y')
        elif len(years) == 1:
            from_date = '{} {}'.format(fp,years[0]).replace('  ',' ').strip()[:11]
            to_date = '{} {}'.format(lp,years[0]).replace('  ',' ').strip()[:11]

            from_date = datetime.strptime(from_date,'%d %b %Y').strftime('%d/%m/%Y')
            to_date = datetime.strptime(to_date,'%d %b %Y').strftime('%d/%m/%Y')
        elif len(years) == 2:
            from_date = '{} {}'.format(fp,years[0]).replace('  ',' ').strip()[:11]
            to_date = '{} {}'.format(lp,years[-1]).replace('  ',' ').strip()[:11]

            from_date = datetime.strptime(from_date,'%d %b %Y').strftime('%d/%m/%Y')
            to_date = datetime.strptime(to_date,'%d %b %Y').strftime('%d/%m/%Y')
        else:
            print(years)


        #Horario 
        horario_box = []
        for i in horario:
            if i not in horario_box:
                horario_box.append(i)
        print(horario_box)
        horario = '  /  '.join( [get_schedule.remove_blank_spaces('{} - {}'.format(i,j)) for (i,j) in zip(horario_box[::2],horario_box[1::2])] )


        yield {
                'From':from_date,
                'To':to_date,
                # 'Desde': desde,
                # 'Hasta': hasta,
                'title/Product_name': title.capitalize().strip(),
                'Place_name/address':'Teatros del Canal',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy': 'https://www.casademexico.es/agenda/',
                'Description':description,
                #'Area': 'Chamberi ',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'4.043.827.900.000.000',
                'longitud':'-37.051.836',
                'Link':link
                
                }
    def get_links_by_scralling(self,url):
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
                box.extend(driver.find_elements_by_xpath('//div[@class="thumbnail-show"]/a'))
                break
            previous_heigth = new_heigth
        box = [i.get_attribute('href') for i in box[1:]]
        driver.close()
        return box