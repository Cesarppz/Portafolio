import scrapy 
import urllib
import subprocess
import re
import logging
from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, tools
from agenda_tools.get_schedule import remove_blank_spaces
logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day

pattern_schedule = re.compile(r'(\d+ \w+( \d+)?)( \d+ \w+ \d+)?')
pattern_horario = re.compile(r'([A-Za-záéíóú]+ \d+ de [A-Za-záéíóú]+)( y \d+ de [A-Za-záéíóú]+)?( a las \d+:\d+)?')


class Webscrape(scrapy.Spider):
    name = 'teatro_espanol_naves'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    start_urls = [  
                 'https://www.teatroespanol.es/programacion?f%5B%5D=area%3A9596',
                 'https://www.teatroespanol.es/programacion?f%5B%5D=area%3A184'
                  ]


    def parse(self, response):
        for url in self.start_urls:
            xpath_links = '//div[@class="node node--type-activity node--view-mode-specific-search ds-1col clearfix"]//div[@class="show-image"]/a[@class="field-group-link link-to-content"]'
            links = tools.get_links_by_scralling(url,xpath_links)
            xpath_image = '//div[@class="node node--type-activity node--view-mode-specific-search ds-1col clearfix"]//div[@class="show-image"]//picture/img'
            image = tools.get_links_by_scralling(url,xpath_image,attribute='src')
            xpath_category = '//div[@class="node node--type-activity node--view-mode-specific-search ds-1col clearfix"]//div[@class="field-name-field-category"]/div[@class="field__item"]'
            category = tools.get_links_by_scralling(url,xpath_category,attribute='text')
            for idx, link in enumerate(links):
                logger.info(f'Link {idx+1}/{len(links)}')
                if link:
                    yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'image':image[idx], 'category':category[idx], 'url':url})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        image = kwargs['image']
        category = kwargs['category']
        url = kwargs['url']

        title = remove_blank_spaces(response.xpath('//h1/text()').get())
        schedule = response.xpath('//span[contains(.,"Fecha")]/following-sibling::div[@class="dates language--es"]//text()').getall()
        description =  response.xpath('//div[@class="clearfix text-formatted field field--name-field-description field--type-text-with-summary field--label-hidden field__item"]//text()').getall() 
        description = remove_blank_spaces(' '.join(description).strip().replace('\n',' ').replace('\xa0',' '))
        horario = response.xpath('//div[@class="field field-name-field-schedule-txt"][contains(.,"Hora")]//p/text()').getall()
        second_try_horario = response.xpath('//div[@class="field field-name-field-schedule-txt"][contains(.,"Hora")]/text()').getall()
        
        #Schedule
        schedule
        fp = remove_blank_spaces(' '.join(schedule[:(len(schedule) -3)]))
        lp = remove_blank_spaces(' '.join(schedule[(len(schedule) - 3):]))
        print(schedule)
        if len(schedule) == 3:
            fp = lp
        # schedule = re.search(pattern_schedule,schedule)
        # fp, lp = schedule.group(1), schedule.group(3)
        if len(fp.split()) == 1:
            fp = '{} {}'.format(fp, ' '.join(lp.split()[1:]))
        if len(fp.split()) == 2:
            fp = '{} {}'.format(fp, lp.split()[-1])

        print(fp)
        print(lp)

        from_date = get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(fp))
        from_date = datetime.strptime(from_date,'%d %b %Y').strftime('%d/%m/%Y')
        to_date = get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(lp))
        to_date = datetime.strptime(to_date,'%d %b %Y').strftime('%d/%m/%Y')

        fp, lp = ' '.join(fp.split()[:2]), ' '.join(lp.split()[:2])

        #name recinto
        if url == 'https://www.teatroespanol.es/programacion?f%5B%5D=area%3A9596':
            name_recinto = 'Naves del Español'
        elif url == 'https://www.teatroespanol.es/programacion?f%5B%5D=area%3A184':
            name_recinto = 'Teatro Español'

        #Image
        print(image)
        image_name = download_images.download(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)
        
        #Category
        category = remove_blank_spaces(category.capitalize())

        category = get_category.chance_category(category)



        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)
        
        #horario
        if horario == []:
            horario = second_try_horario
        
        horario = '  /  '.join([remove_blank_spaces(i) for i in horario if re.search(re.compile(r'\d{2,}h'),i)] )

        yield {
                'From':from_date,
                'To':to_date,
                # 'Desde':fp,
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':name_recinto,
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
                'latitud':'403.921.739',
                'longitud':'-3.697.394',
                'Link':link
                
                }
