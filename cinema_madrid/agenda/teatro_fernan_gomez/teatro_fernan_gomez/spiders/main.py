import scrapy 
import re
import logging
import datetime as dt
from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, months
from agenda_tools.get_schedule import remove_blank_spaces


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_eng_adv = months.dict_of_months_adv_spanish_to_english 

pattern = re.compile(r'\w+. \w+. \d+')
pattern_schedule = re.compile(r'((\d+,\s)?\d+\sd?e?\s?(\w+)?( de \d+)?( al)?( \d+\s?d?e? \w+\,?\s?d?e?\s?(\d+)?)?)')
comma_schedule =  re.compile(r'\d+, \d+')
url_category_pattern = re.compile(r'^https.*/(.*)$')

base_link = 'https://www.teatrofernangomez.es'

class Webscrape(scrapy.Spider):
    name = 'teatro_fernan_gomez'
    logger = logging.getLogger(name)

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    start_urls = [  
                  'https://www.teatrofernangomez.es/programacion/teatro',
                  'https://www.teatrofernangomez.es/programacion/danza',
                  'https://www.teatrofernangomez.es/programacion/musica',
                  'https://www.teatrofernangomez.es/programacion/exposiciones',
                  'https://www.teatrofernangomez.es/programacion/cine',
                  'https://www.teatrofernangomez.es/programacion/infantil-juvenil'
                  ]


    def parse(self, response):
        category = re.match(url_category_pattern,response.request.url).group(1)
        print(category)
        links = set(response.xpath('//div[@class="padding-wrapper"]/a/@href').getall())
        for idx,link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                link = '{}{}'.format(base_link,link)
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'category':category})


    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        category = kwargs['category'].capitalize()

        title =  response.xpath('//h1/text()').get().strip()
        schedule = response.xpath('//div[@class="sidebar-wrap"]/div[@class="field field--name-field-schedule-tip field--type-string field--label-hidden field__item"]/text()').get()
        horario = response.xpath('//div[@class="sidebar-wrap"]/div[@class="clearfix text-formatted field field--name-field-schedule-txt field--type-text-long field--label-inline"]/div[@class="field__item"]/p/text()').get()
        description = response.xpath('//div[@class="clearfix text-formatted field field--name-field-photo-foot field--type-text-longfield--label-hidden field__item"]/p//text()').getall()
        description = ' '.join(description)
        image = response.xpath('//div[@class="field field--name-field-media-image field--type-image field--label-hidden field__item"]/picture/img/@src').get()
        image = '{}{}'.format(base_link,image)
        
        
        #Schedule
        print('Schedule : ',schedule)
        schedule = get_schedule.clean_schedule(schedule,pattern_schedule)
        if type(schedule) is not tuple:
            schedule = get_schedule.clean_schedule(schedule,pattern_schedule,split_pattern='y')
            if re.match(comma_schedule,schedule[0]):
                schedule = list(schedule)
                schedule[0] = schedule[0].split(',')[0]
        print(schedule)

        if type(schedule) == str:
            fp = schedule
            lp = schedule
        else:
            fp, lp = schedule
            fp, lp = get_schedule.eliminar_de_not_list(fp), get_schedule.eliminar_de_not_list(lp)
        change_year = False

        if len(get_schedule.remove_blank_spaces(fp).split()) == 2 and len(get_schedule.remove_blank_spaces(lp).split()) == 3:
            fp = '{} {}'.format(fp,get_schedule.remove_blank_spaces(lp).split()[-1])
        elif len(get_schedule.remove_blank_spaces(fp).split()) == 2 and len(get_schedule.remove_blank_spaces(lp).split()) ==2:
            fp = '{} {}'.format(fp,year)
            lp = '{} {}'.format(lp,year)
            change_year = True
        elif len(get_schedule.remove_blank_spaces(fp).split()) == 1 and len(get_schedule.remove_blank_spaces(lp).split()) == 2:
            fp = '{} {} {}'.format(fp,remove_blank_spaces(lp).split()[1],year)
            lp = '{} {}'.format(lp,year)
            change_year = True
        elif len(get_schedule.remove_blank_spaces(fp).split()) == 1 and len(get_schedule.remove_blank_spaces(lp).split()) == 3:
            fp = '{} {} {}'.format(fp,remove_blank_spaces(lp).split()[1],remove_blank_spaces(lp).split()[-1])
        
        fp, lp = remove_blank_spaces(fp), remove_blank_spaces(lp)
        print('Fp :',fp)
        print('LP :',lp)
        from_date = datetime.strptime(get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(fp)), '%d %b %Y')
        to_date =  datetime.strptime(get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(lp)), '%d %b %Y')
        
        if change_year == True:
            if from_date.month < mes and to_date.month < mes:
                from_date = from_date + dt.timedelta(days=365)
                to_date = to_date + dt.timedelta(days=365)
            elif from_date.month < mes and to_date.month >= mes:
                from_date = from_date + dt.timedelta(days=365)
            elif to_date.month < mes and from_date.month >= mes:
                to_date = to_date + dt.timedelta(days=365)
        
        fp = get_schedule.transform_to_adv_eng_spa(from_date.strftime('%d %b'))
        lp =  get_schedule.transform_to_adv_eng_spa(to_date.strftime('%d %b'))
        from_date = from_date.strftime('%d/%m/%Y')
        to_date = to_date.strftime('%d/%m/%Y')

        #Image
        image_name = download_images.download(image,idx='{}_{}'.format(category,idx),len_links=len_links, nombre_del_lugar='{}'.format(self.name))

        #description 
        if description == '\xa0':
            description = response.xpath('//div[@class="row row-wrap"]/div[@class="col-md-12"]/p//text()').getall()
            description = ' '.join(description).replace('\xa0','').replace('  ',' ').strip()

        #category 
        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        #horasio 
        if horario:
            horario = horario.replace(' – ','  /  ').replace('horas cada día.','')

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde':f'Desde {fp}',
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Teatro Fernán Gómez',
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
                'latitud':'4.042.463.300.000.000',
                'longitud':'-36.898.599',
                'Link':link
                
                }
