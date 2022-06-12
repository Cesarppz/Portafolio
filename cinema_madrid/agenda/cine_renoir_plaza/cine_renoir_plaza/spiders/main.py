import scrapy 
import urllib
import subprocess
import re
import logging
from datetime import datetime
from agenda_tools import get_title, get_schedule, download_images, get_category, months
logger = logging.getLogger()
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_spa_adv = months.dict_of_months_adv_spanish_to_spanish

link_image_pattern = re.compile(r'^(https?).*/(.+\.(jpg|jpeg|png))')
patter_links = re.compile(r'https://www.cinesrenoir.com/cine/([\-\w]+)/cartelera/')
pattern_schedule = re.compile(r'(\d+\s+de\s+\w+)')


class Webscrape(scrapy.Spider):
    name = 'cine_renoir_plaza'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv'
                        }

    def start_requests(self):
        urls = ['https://www.cinesrenoir.com/cine/renoir-plaza-de-espana/cartelera/',
                  'https://www.cinesrenoir.com/cine/cines-princesa/cartelera/',
                  'https://www.cinesrenoir.com/cine/renoir-retiro/cartelera/']

        for url in urls:
            r_name = re.match(patter_links,url).group(1)
            yield scrapy.Request(url, callback=self.parse, cb_kwargs={'recinto_name':r_name})


    def parse(self, response, **kwargs):
        recinto_name = kwargs['recinto_name']
        links = set(response.xpath('//div[@class="my-account-content mb-15 d-none d-md-block d-lg-none"]//div[@class="col-9"]/a/@href').getall())
        for idx, link in enumerate(links):
            logger.info(f'Link {idx+1}/{len(links)}')
            if link:
                yield response.follow(link, callback=self.new_parse, cb_kwargs={'link':link, 'idx':idx+1,'len':len(links),'recinto_name':recinto_name})

    def new_parse(self, response, **kwargs):
        recinto_name = kwargs['recinto_name']
        link = kwargs['link']
        len_links = kwargs['len']
        idx = kwargs['idx']

        title =  response.xpath('//div[@class="single_product_desc"]/h4/text()').get()
        schedule =response.xpath('//div[@class="short_overview mb-4" and contains(.,"Estreno")]//p/text()').get()
        image = response.xpath('//div[@class="single_product_thumb mb-15"]/a/img/@src').get()
        description = response.xpath('//div[@class="d-none d-md-block short_overview mb-4" and contains(.,"Sinopsis")]//p/text()').get()
        horario = response.xpath('//div[@class="shortcodes_content"]//h6/text()').getall()
        category = list(set(response.xpath('//div[@class="shortcodes_content"]//div[@class="col-3 align-self-center"]//small/text()').getall()))[0]
        category = category.replace('Original Castellano','Cine').replace('Original subtitulada a Castellano','Cine V.O.')

        fp = re.search(pattern_schedule, horario[0]).group(1).replace('de','').replace('  ',' ')
        lp = re.search(pattern_schedule, horario[-1]).group(1).replace('de','').replace('  ',' ')
        fp = get_schedule.transform_to_adv(fp)
        lp = get_schedule.transform_to_adv(lp)
        from_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(fp), year), '%d %b %Y').strftime('%d/%m/%Y')
        to_date = datetime.strptime('{} {}'.format(get_schedule.transform_to_adv_spa_eng(lp), year), '%d %b %Y').strftime('%d/%m/%Y')
        #schedule_list = get_schedule.eliminar_de(schedule_list)

        #Image
        image_name = download_images.download(image,idx=idx,len_links=len_links, nombre_del_lugar=self.name)

        #Category
        id_category = get_category.id_category(category)

        main_category = get_category.main_category(category)
        

        #Nombre lugar
        if recinto_name == 'cines-princesa':
            recinto_name = 'Princesa'
        elif recinto_name == 'renoir-retiro':
            recinto_name = 'Retiro'
        elif recinto_name == 'renoir-plaza-de-espana':
            recinto_name = 'Plaza de España'

        #Horario 
        
        horario_box = []
        n_horarios = len(response.xpath('//div[@class="shortcodes_content"]//div[@class="my-account-content  d-none d-md-block"]/div[@class="row"]'))
        for i in range(1, n_horarios + 1):
             horario_part = response.xpath(f'//div[@class="shortcodes_content"][{i}]//div[@class="my-account-content  d-none d-md-block"]/div[@class="row"]//div[@class="text-center"]/span[position()=2]/a/text()').getall()
             horario_box.append(' - '.join(horario_part))

        horario = list(zip(horario,horario_box))
        horario = ' / '.join([' '.join(x) for x in horario])
        horario = re.sub('del \d+','',horario)
        #print([ ' '.join(x) for j in horario for x in j])
        #horario = ' '.join(list(zip(horario,horario_box)))
            
        if recinto_name == 'Plaza de España' or recinto_name == 'Princesa':
            yield{
                'From':from_date,
                'To':to_date,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Cine Renoir {}'.format(recinto_name),
                'Categoria' :category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy':'https://www.cinesrenoir.com{}'.format(link),
                'Description':description,
                'City':'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'404.243.792',
                'longitud':'-37.133.863',
                'Link':'https://www.cinesrenoir.com{}'.format(link)
            }

        elif recinto_name == 'Retiro':

            yield{
                'From':from_date,
                'To':to_date,
                'title/Product_name': title.capitalize(),
                'Place_name/address':'Cine Renoir {}'.format(recinto_name),
                'Categoria': category,
                'Title_category':main_category,
                'Nº Category': id_category,
                'image':image_name,
                'Hours':horario,
                'Link_to_buy':'https://www.cinesrenoir.com{}'.format(link),
                'City': 'Madrid',
                'Province': 'Madrid',
                'Country':'España',
                'latitud':'404.243.792',
                'longitud':'-37.133.8630',
                'link':'https://www.cinesrenoir.com{}'.format(link)
            }
