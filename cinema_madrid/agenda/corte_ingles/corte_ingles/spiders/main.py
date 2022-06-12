import scrapy 
from scrapy.crawler import CrawlerProcess
import urllib
import subprocess
import re
from agenda_tools import get_title,get_schedule,download_images, get_category
import logging
from datetime import datetime
import datetime as dt
logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

link_image_pattern = re.compile(r'^.*/(.+\.(jpg|jpeg|png))')
patter_links = re.compile(r'^(http).*//.*\/((exposiciones|cine-en-casa-de-mexico|literatura|familias|teatro))/.*')
p3 = re.compile(r'//(.*)')
schedule_pattern = re.compile(r'(\d+\sde\s\w+)')
schedule_pattern2 = re.compile(r'al\s(\d+\sde\s\w+)')
part_image  = re.compile(r'^.*net/(.+\.(jpg|jpeg|png)).*')
falt = 'https://ocms.expertustech.es/opencms/'

class Webscrape(scrapy.Spider):
    name = 'corte_ingles'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings={
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}

    start_urls = ['https://www.elcorteingles.es/entradas/channels/teatro-amaya']


    def parse(self, response):
        links = set(response.xpath('//ul[@class="item-search__list"]//a/@href').getall())
        for idx, link in enumerate(links):
            if link:
                logger.info(f'Link {idx+1}/{len(links)}')
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link,'idx':idx+1,'len':len(links)})

    def new_parse(self, response, **kwargs):
        link = kwargs['link']
        idx = kwargs['idx']
        len_links = kwargs['len']
        title = response.xpath('//div[@class="content-product__purchase-content c-border-color"]/h1/text()').get()
        schedule = response.xpath('//div[@class="content-product__purchase c-background"]//div[@class="margin-xxs content-product__50text text"]/text()').get()
        horario = response.xpath('//div[@class="content-product__desc-item"]//p[position()=2]/text()').get()
        image = response.xpath('//div[@class="content-product__img-wrapper"]//img/@src').get()
        image = re.match(p3, image).group(1)
        image = falt + re.match(part_image, image).group(1)
        description = response.xpath('//dt[contains(.,"Más información")]/following-sibling::*//p//text()').getall()
        description = ' '.join(description)
        buy_link = response.xpath('//div[@class="product-header__buy"]/a/@href').get()

        
        fp = re.search(schedule_pattern,schedule).group(1)
        fp = get_schedule.eliminar_de_not_list(fp)
        fp = fp.replace('de 2021','').strip()
        lp = fp
        try:
            lp = re.search(schedule_pattern2,schedule).group(1)
            lp = get_schedule.eliminar_de_not_list(lp)
            lp = lp.replace('de 2021','').strip()
        except Exception:
            pass
            #Titulo completo
        #large_title = get_title.make_title(title,'Teatro amaya',fp_schedule=fp,lp_schedule=lp)

            #Descargar la imagen
        image_name = download_images.download_opener(image,nombre_del_lugar='corte_ingles',idx=idx,len_links=len_links)
            
        category = 'Teatro'
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)

        fp = get_schedule.transform_to_adv(fp)
        lp = get_schedule.transform_to_adv(lp)
        from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(fp), year), '%d %b %Y').strftime('%d/%m/%Y')
        to_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(lp), year), '%d %b %Y')
        if to_date.month < mes:
            to_date = to_date = dt.timedelta(days=365)
        to_date = to_date.strftime('%d/%m/%Y')


        yield { 
                'From':from_date,
                'To':to_date,
                # 'Desde':fp,
                # 'Hasta':lp,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Teatro Amaya',
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
                'latitud':'404.351.314',
                'longitud':'-3.697.144.899.999.990',
                'Link':link

            }
      