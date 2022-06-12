#import enum
import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
import datetime as dt
from datetime import datetime
from agenda_tools import get_schedule, get_title,download_images, get_category,months

schedule_pattern = re.compile(r'\d+/\d+')
back_link  = 'https://www.cinepazmadrid.es/'
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_days_of_week = months.week_days
day_week = dict_days_of_week[datetime.now().weekday()]
if day_week == 'Domingo':
    next_day_week = 'Lunes'
else:
    next_day_week = dict_days_of_week[datetime.now().weekday() + 1]
tomorrow = dt.date.today() + dt.timedelta(days=1)
fecha_actual = '{}/{}'.format(dia,mes)
fecha_tomorrow = '{}/{}'.format(tomorrow.day,tomorrow.month)

class Webscrape(scrapy.Spider):
    name = 'cine_paz'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}

    start_urls = ['https://www.cinepazmadrid.es/es/cartelera']


    def parse(self, response):
        links = response.xpath('//div[@class="col-md-8 events-column izquierda clearfix"]//div[@class="col-sm-8 col-xs-7"]//a/@href').getall()
        links = set(links)
        for idx, link in enumerate(links):
            yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links)})
    




    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        title = response.xpath('//div[@class="row marginL0 marginR0"]/div[@class="text-header2 gibsonT"]/span/text()').get().strip()
        image = response.xpath('//div[@class="col-xs-5 relativo"]//img/@src').get()
        description = response.xpath('//div[@class="col-xs-12 paddingL0 paddingR0"]/span[@class="sinopsis gibsonL"]/text()').get().strip()
        schedule = response.xpath('//div[@class="contenedor_horarios"]//text()').getall()

        #Titulo completo
        #large_title = get_title.make_title(title,place_name='Cine Paz')

        #Descargar la imagen
        
        image = back_link + image 
        image_name = download_images.download(image,nombre_del_lugar='cine_paz',idx=idx,len_links=len_links)

        if title[-6:] == '(vose)':
            category = 'Cine V.O.'
        else:
            category = 'Cine'

        #schedule 
        clean_schedule = []
        for i in schedule:
            dates = i.replace('\n','').replace('\t','').replace('Hoy',fecha_actual).replace('Mañana',fecha_tomorrow)
            clean_schedule.append(dates)
        for i in clean_schedule:
            try:
                clean_schedule.remove('')
            except:
                break
        #print(clean_schedule)
        fechas = get_schedule.schedule_in_list(clean_schedule,schedule_pattern)
        horario = ' '.join(schedule)
        horario = horario.replace('\t\t','').replace('\n\t','').replace('\n','').strip().split('\t')
        horaio_dias =  [i for i in horario[::2]]
        horaio_h =  [i.strip().replace(' ',', ') for i in horario[1::2]]
        horario = list(zip(horaio_dias,horaio_h))
        horario = ['a las '.join(i) for i in horario]
        horario = ' / '.join(horario).replace('Hoy','{} {}'.format(day_week,fecha_actual)).replace('Mañana','{} {}'.format(next_day_week,fecha_tomorrow))

        fp = datetime.strptime(fechas[0],'%d/%m').strftime('%d %b')
        lp = datetime.strptime(fechas[-1],'%d/%m').strftime('%d %b')
        fp_from = datetime.strptime(fechas[0],'%d/%m').strftime(f'%d/%m/{year}')
        lp_from = datetime.strptime(fechas[-1],'%d/%m').strftime(f'%d/%m/{year}')
        fp = get_schedule.transform_to_adv_eng_spa(fp)
        lp = get_schedule.transform_to_adv_eng_spa(lp)
        #Categroria
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)


        yield  {
            'From':fp_from,
            'To':lp_from,
            'title/Product_name': title.capitalize(),
            'Place_name/address':'Cines Paz',
            'Categoria':category,
            'Title_category':main_category,
            'Nº Category': id_category,
            'image':image_name,
            'Hours':horario,
            'link_to_buy':'https://www.cinepazmadrid.es/es/cartelera',
            'Description':description,
            'City': 'Madrid',
            'Province': 'Madrid',
            'Country':'España',
            'latitud':'4.043.086.479.999.990',
            'longitud':'-37.033.987',
            'Link':link
        }
      