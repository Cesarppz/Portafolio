#encoding=utf-8
import scrapy 
import re
import logging
from scrapy_splash import SplashRequest
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
pattern_schedule = re.compile(r'((\d+,\s)?\d+\sd?e?\s?(\w+.?)?( de \d+)?( al)?( y)?( \d+\s?d?e? \w+.?\,?\s?d?e?\s?(\d+)?)?)')
comma_schedule =  re.compile(r'\d+, \d+')
url_category_pattern = re.compile(r'^https.*/(.*)$')


class Webscrape(scrapy.Spider):
    name = 'teatro_alfil'
    logger = logging.getLogger(name)

    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }
    start_urls = [  
                  'https://teatroalfil.es/'
                  ]

    # def starts_url(self, url, **kwargs):
    #     url = url.request.url
    #     yield SplashRequest(url=url, callback=self.new_parse, cb_kwargs=kwargs)


    def parse(self, response):
        images = response.xpath('//div[@class="vc_gitem-zone vc_gitem-zone-a vc_gitem-is-link"]/img/@src').getall()
        links = set( response.xpath('//a[@class="vc_gitem-link vc-zone-link"]/@href').getall())
        assert (links != set()), 'List of link is empty'
        for idx,link in enumerate(links):
            self.logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                #link = '{}'.format(link.encode('utf-8').strip())
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'image':images[idx]})


    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        image = kwargs['image']
        print(link)


        title =  response.xpath('//h1/text()').get().strip()
        schedule = response.xpath('//div[@class="vc_message_box vc_message_box-solid vc_message_box-square vc_color-grey"]/div[@class="vc_message_box-icon"]/i[@class="fa fa-calendar"]/../../text()').get()
        horario = (response.xpath('//div[@class="vc_message_box vc_message_box-solid vc_message_box-square vc_color-grey"]/div[@class="vc_message_box-icon"]/i[@class="fa fa-ticket"]/../../text()').get() + 
                   ' '+response.xpath('//div[@class="vc_message_box vc_message_box-solid vc_message_box-square vc_color-grey"]/div[@class="vc_message_box-icon"]/i[@class="fa fa-clock-o"]/../../text()').get())
        description = response.xpath('//div[@class="wpb_text_column wpb_content_element "]/div[@class="wpb_wrapper"]/p[position()=1]/text()').getall()
        description = ' '.join(description)

        
        
        #Schedule
        all_sesson = False
        if schedule.strip() == 'Toda la temporada':
            schedule = '28 Diciembre 2021'
            all_sesson = True
        print('Schedule : ',schedule)
        schedule = schedule.replace('Del','').replace('del','').replace('Desde','').replace('De','').replace('de','').replace('el','').replace('El','').replace('Hasta','')
        
        switch = False
        if 'Hasta' in schedule:
            schedule.replace('Hasta','')
            switch = True
        
        schedule_split = schedule.split('al')
        if len(schedule_split) == 1:
            schedule_split = schedule_split[0].split('y')

        fp , lp = schedule_split[0], schedule_split[-1]
        chanced_year = False

        #Separar por coma
        if ',' in fp:
            fp = fp.split(',')[0]
        if ',' in lp:
            lp = lp.split(',')[-1]
        fp, lp = remove_blank_spaces(fp), remove_blank_spaces(lp)
        #Solo numero 
        if len(fp.split()) == 1:
            fp = '{} {} {}'.format(fp,lp.split()[1], year)
        #Missing year
        elif len(fp.split()) == 2:
            fp = '{} {}'.format(fp,year)
            chanced_year = True
        #lp missing year
        if len(lp.split()) == 2:
            lp = '{} {}'.format(lp,year)
            chanced_year = True
        
        print(fp)
        print(lp)
        try:
            fp = get_schedule.transform_to_adv(fp)
            lp = get_schedule.transform_to_adv(lp)
        except Exception:
            pass

        from_date = datetime.strptime(get_schedule.transform_to_adv_spa_eng(fp),'%d %b %Y')
        to_date = datetime.strptime(get_schedule.transform_to_adv_spa_eng(lp),'%d %b %Y')

        if chanced_year:
            if from_date.month < mes and to_date.month < mes:
                from_date = from_date + dt.timedelta(days=365)
                to_date = to_date + dt.timedelta(days=365)

            elif from_date.month < mes and to_date.month >= mes:
                from_date = from_date + dt.timedelta(days=365)

            elif to_date.month < mes and from_date.month > mes:
                to_date = to_date + dt.timedelta(days=365)

        if switch:
            fp, from_date = None, None

        from_date = from_date.strftime('%d/%m/%Y')
        to_date = to_date.strftime('%d/%m/%Y')

        if all_sesson:
            fp = 'Toda la temporada'
            lp = 'Toda la temporada'
            from_date = None
            to_date = None
        else:
            fp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(fp))
            lp = get_schedule.transform_to_adv_eng_spa(get_schedule.transform_to_adv_spa_eng(lp))
            fp = ' '.join(fp.split()[:2])
            lp = ' '.join(lp.split()[:2])

        #Image
        
        image_name = download_images.download(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)
            # try:
            #     image_name = download_images.download_image_with_requests(image.encode('ascii','ignore'),idx=idx,len_links=len_links, nombre_del_lugar=self.name)
            # except Exception:
            #     image_name = download_images.download_opener(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #description 
        if description == '\xa0':
            description = response.xpath('//div[@class="row row-wrap"]/div[@class="col-md-12"]/p//text()').getall()
            description = ' '.join(description).replace('\xa0','').replace('  ',' ').strip()

        #category 
        category = 'Teatro'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde':f'Desde {fp}',
                # 'Hasta': lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Teatro Alfil',
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
                'latitud':'4.042.318',
                'longitud':'-370.452',
                'Link':link
                
                }
