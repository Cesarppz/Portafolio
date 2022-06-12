import scrapy 
from scrapy_splash import SplashRequest
import urllib
import subprocess
import re
import datetime as dt
from datetime import datetime
from agenda_tools import get_schedule,download_images, get_category

schedule_pattern = re.compile(r'\d+/\d+')
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
tomorrow = dt.date.today() + dt.timedelta(days=1)
fecha_actual = '{}/{}'.format(dia,mes)
fecha_tomorrow = '{}/{}'.format(tomorrow.day,tomorrow.month)

class Webscrape(scrapy.Spider):
    name = 'honky_tonk'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}


    def start_requests(self):
        url = 'https://clubhonky.com/programacion/'

        yield SplashRequest(url=url, callback=self.parse )


    def parse(self, response):
        schedule =  response.xpath('//div[@class="t_line_m"]/a[@class="t_line_node"]/@href').getall() 
        schedule = [i.replace('#','').strip() for i in schedule]
        horario =  response.xpath('//div[@class="textwidget schedule_widget"]/p//text()').getall()
        horario_f = [get_schedule.remove_blank_spaces(' '.join(i)) for i in list(zip(horario[::2],horario[1::2]))]
        if len(horario_f) < len(horario[::2]):
            horario_f.append(horario[::2][-1])
        horario_f = ' - '.join(horario_f)

        for idx, date in enumerate(schedule):
            self.logger.info('Scraper {}/{}'.format(idx,len(schedule)))
            link =  response.xpath(f'//div[@class="item"][@data-id="{date}"]/a/@href').get()
            title = response.xpath(f'//div[@class="item"][@data-id="{date}"]/@data-description').get().lower().capitalize()
            link = 'http://localhost:8050/render.html?url={}'.format(link)

            yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(schedule), 'date':date, 'title':title,'horario':horario_f})
                

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        date = kwargs['date']
        title = kwargs['title']
        #horario = kwargs['horario']

        image = response.xpath('//figure/img/@src').get()

        
        description = ' '.join(response.xpath('//div[@class="pre_next_concierto"]/following-sibling::p/text()').getall()[:2])
        horario =  response.xpath('//*[@class="hora_concierto_destacado"]/text()').get()
        

        #Descargar la imagen

        image_name = download_images.download(image,nombre_del_lugar='honky_tonk',idx=idx,len_links=len_links)

        #schedule 

        #print(clean_schedule)
        fp = datetime.strptime(date,'%d/%m/%Y').strftime('%d %b')
        fp = get_schedule.transform_to_adv_eng_spa(fp)
        lp = fp
       
        fp_from = date
        lp_from = date

        #Categroria
        category = 'Música'
        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        

        yield {     'From':fp_from,
                    'To':lp_from,
                    # 'Desde':fp,
                    # 'Hasta':lp,
                    'title/Product_name': title.capitalize(),
                    'Place_name/address':'Honky Tonk',
                    'Categoria' : category,
                    'Title_category':main_category,
                    'Nº Category': id_category,
                    'image':image_name,
                    'Hours':horario,
                    'Link_to_buy': link,
                    'Description':description,
                    #'Area': 'Chamberi ',
                    'City': 'Madrid',
                    'Province': 'Madrid',
                    'Country':'España',
                    'latitud':'424.657.256',
                    'longitud':'-709.319.009',
                    'Link':link}