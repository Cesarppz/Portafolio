import scrapy 
import re
import logging
from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, months
from agenda_tools.get_schedule import transform_to_adv
import datetime as dt
logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_eng_adv = months.dict_of_months_adv_spanish_to_english 
base_link = 'https://teatrosohoclub.com/'
pattern = re.compile(r'\w+. \w+. \d+')
pattern_schedule = re.compile(r'(\d+( de )?([A-Za-záéíóú]+)?( al \d+ de [A-Za-záéíóú]+)?)')
# pattern_schedule = re.compile(r'del (\d+ de ([A-Za-záéíóú]+)?( al \d+ de [A-Za-záéíóú]+)?)')

class Webscrape(scrapy.Spider):
    name = 'soho_club'

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    start_urls = [  
                  'https://teatrosohoclub.com/--sala-principal.php',
                  'https://teatrosohoclub.com/--biblioteca.php'
                  ]


    def parse(self, response):
        images = response.xpath('//div[@class=""]//img/@src').getall()[::2]
        links = set(response.xpath('//div[@class=""]//a/@href').getall())
        for idx,(link, images) in enumerate(zip(links,images)):
            logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                link = '{}{}'.format(base_link,link)
                image = '{}{}'.format(base_link,images)
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links), 'image':image})


    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        image = kwargs['image']
        title =  response.xpath('//div[@class=""]//p[@style="text-align:left; font-size:1.2em;"]//text()').get().strip().capitalize()
        schedule =  response.xpath('//div[contains(.,"FECHA")]/following-sibling::div/div/p//text()').get()
        description =  response.xpath('//div[@class="text-inner"]/div[contains(.,"SINOPSIS")]/following-sibling::div//text()').getall()
        category =  response.xpath('//div[contains(.,"GÉNERO")]/following-sibling::div/div/p//text()').get()
        horario =  response.xpath('//div[@id="comprar"]//div[@style="float:left; padding-left:5px;"]//text()').getall()
        horario_time  = response.xpath('//div[@style="float:left; padding-top:2px;"]//text()').getall()#Las horas de los horarios
        
        #title 
        # title = ' '.join([i.strip() for i in title])

        #Schedule
        # try:
        schedule = re.search(pattern_schedule,schedule).group(1)
        schedule = schedule.replace('de','').replace('  ',' ').strip()
        schedule = schedule.split('al')
        if len(get_schedule.remove_blank_spaces(schedule[0])) <= 2:
            fp = '{} {}'.format(schedule[0],schedule[-1].split()[-1])
            fp = get_schedule.remove_blank_spaces(fp)
            lp = get_schedule.remove_blank_spaces(schedule[-1])
        else:
            fp = get_schedule.remove_blank_spaces(schedule[0])
            lp = get_schedule.remove_blank_spaces(schedule[-1])
        

        from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(transform_to_adv(fp)), year), '%d %b %Y')
        to_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(transform_to_adv(lp)), year), '%d %b %Y')
        
        if from_date.month < mes and to_date.month < mes :
            from_date = from_date + dt.timedelta(days=365)
            to_date = to_date + dt.timedelta(days=365)
        elif from_date.month < mes and to_date.month >= mes:
            from_date = from_date + dt.timedelta(days=365)
        elif to_date.month < mes and from_date.month >= mes:
            to_date = to_date + dt.timedelta(days=365)

        from_date = from_date.strftime('%d/%m/%Y')
        to_date = to_date.strftime('%d/%m/%Y')

        #Hours
        comienzo_list = 0
        final_list = 3
        horario_clean = []
        for i in range(len(horario)//3):
            horario = ' '.join(horario[comienzo_list:final_list])
            horario_clean.append(' - '.join([horario,horario_time[i]]))
            comienzo_list += 3
            final_list += 3

        horario_clean = '  /  '.join(horario_clean)
        #Image
        image_name = download_images.download(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #description 
        description = ' '.join(description) 

        #category
        teatro_pattern = re.compile(r'teatro')
        if re.search(teatro_pattern,category.lower()):
            category = 'Teatro'
        category = get_category.chance_category(category)
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde': fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Teatro Soho Club',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario_clean,
                'Link_to_buy': link,
                'Description':description,
                #'Area': 'Center',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'40.422.586',
                'longitud':'-37.119.272',
                'Link':'{}{}'.format(base_link,link)
                
                }
