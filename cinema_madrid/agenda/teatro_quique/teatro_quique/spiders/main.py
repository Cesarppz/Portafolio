import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
from agenda_tools import download_images, get_schedule, get_title, get_category, months
from datetime import datetime
import logging

logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
dict_trans = months.dict_of_months_adv_spanish_to_english

get_link = re.compile(r'background-image.*url\((https?.*/.+\.(jpg|jpeg|png))')
link_image_pattern = re.compile(r'^(https?).*/(.+\.(jpg|jpeg|png))')
horario_patter = re.compile(r'((Del)?\s?\d+\s([A-Za-z]+)?\s?(\w+)?\s?al\s\d+\s[A-Za-z]+ (de )?(\d+))')


class Webscrape(scrapy.Spider):
    name = 'teatro_quique'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}

    start_urls = ['https://teatroquiquesanfrancisco.es/cartelera-adulto/']


    def parse(self, response):
        links = set(response.xpath('//div[@class="work-info"]/a/@href').getall())
        for idx , link in enumerate(links):
            if link:
                logger.info(f'Link {idx+1}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link,'idx':idx+1,'len':len(links)})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']
        title = response.xpath('//div[@class="content"]/h2/text()').get()
        schedule = response.xpath('//div[@class="iwt-text"]/p/text()').get()
        horario = response.xpath('//div[@class="iwt-text"]/p/text()').getall()[1]
        image = response.xpath('//div[@class="image-bg"]/@style').get()
        image = re.match(get_link, image).group(1)
        description =  response.xpath('//div[@class="wpb_wrapper"]/p[contains(.,"Sinopsis")]/following-sibling::p//text()').getall()
        description = ' '.join(description).replace('\n',' ').replace('\xa0','').replace('  ',' ').strip()
        buy_link = response.xpath('//a[@class="nectar-button large see-through-2 "]/@href').get()
        print(schedule)
        fp, lp = get_schedule.clean_schedule(schedule,horario_patter)
        try:
            fp = fp.replace('De','')
            lp = lp.replace('de','')
        except Exception as e:
            pass
        
        desde = fp
        hasta = lp
        if len(fp) <= 2:
            desde = f'{fp} {lp[3:6]}'
            fp = f'{fp} {lp[3:]}'
        elif len(fp) > 2 and len(fp) <=6:
            fp = f'{fp} {lp[6:]}'
        elif len(fp) > 6:
            desde = fp[:6]
        if len(lp) > 6:
            hasta = lp[:6]

        fp = fp.replace('  ',' ').strip()
        fp = fp.split()
        lp = lp.replace('  ',' ').strip()
        lp = lp.split()

        fp[1] = dict_trans[fp[1].capitalize()]
        fp = ' '.join(fp)
        lp[1] = dict_trans[lp[1].capitalize()]
        lp = ' '.join(lp)
        date_fp = datetime.strptime(fp,'%d %b %Y').strftime('%d/%m/%y')
        date_lp = datetime.strptime(lp,'%d %b %Y').strftime('%d/%m/%y')
        #large_title = get_title.make_title(title, 'Teatro quique',fp_schedule=fp,lp_schedule=lp)
        image_name = download_images.download(image,nombre_del_lugar='teatro_quique',idx=idx,len_links=len_links) 

        category = 'Teatro'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        yield { 'From':date_fp,
                'To':date_lp,
                # 'Desde':f'Desde {desde}',
                # 'Hasta':hasta,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Teatro Quique San Francisco',
                'Categoria' : category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy': buy_link,
                'Description':description,
                #'Area': 'Chamberi ',
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'404.337.248',
                'longitud':'-37.112.857',
                'Link':link

            }
      