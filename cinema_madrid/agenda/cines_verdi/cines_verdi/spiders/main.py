import scrapy 
from scrapy_splash import SplashRequest
import urllib
import subprocess
import re
import traceback
from agenda_tools import download_images, get_schedule, get_title, get_category
from datetime import datetime
mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year


schedule_pattern_words = re.compile(r'[A-Za-záéíóúñ]+')
schedule_pattern_numbers = re.compile(r'[0-9]+/[0-9]+')


class Webscrape(scrapy.Spider):
    name = 'cines_verdi'
    #allowed_domains = ['www.cinescallao.es']
    custom_settings= {
                        'FEED_URI':f'results_{name}_{dia}_{mes}.csv',
                        'FEED_FORMAT':'csv',
                        'FEED_EXPORT_ENCODING':'utf-8'}



    def start_requests(self):
        url = 'https://madrid.cines-verdi.com/cartelera'

        yield SplashRequest(url=url, callback=self.parse )

    def parse(self, response):
        title =  response.xpath('//div[@class="col-md-8"]/h2/a/text()').getall()
        category = response.xpath('//div[@class="col-md-8"]/h2/a/small/text()').getall()
        #schedule = response.xpath('//div[@class="col-sm-9 col-12"]//div[@class="fecha"]/text()').getall()
        image =  response.xpath('//div[@class="col-md-4"]//img[position()=1]/@src').getall()
        description =  response.xpath('//div[@class="col-md-8"]//p/text()').getall()

        for idx  in range(len(category)):
            print(f'Link {idx+1}')
            fp = None
            lp = None
            try:
                if category[idx] == 'VOSE':
                    category[idx] = 'Cine V.O.'
                elif category[idx] == 'VO':
                    category[idx] = 'Cine V.O.'
                else:
                    category[idx] = 'Cine'
                
                # Description
                description = response.xpath(f'//article[{idx+1}]/div[2]/p/text()').get().replace('\n','')


                image_name = download_images.download_opener(image[idx], nombre_del_lugar='cines_verdi', idx=idx+1, len_links=len(image))
                id_category = get_category.id_category(category[idx])
                main_category =  get_category.main_category(category[idx])
                #   Mover la imagen a la carpeta de imagenes
                schedule  = response.xpath(f'//article[{idx+1}]/div[2]/div[2]/ul//text()').getall()
                horario_s = response.xpath(f'//article[{idx+1}]/div[2]/div[2]/div//text()').getall()
                #print('Schedule Hoarios:',horario_s)
                #horario_word = horario_s[0]
                horario_s = get_schedule.remove_blank_spaces(' '.join(horario_s[1:]))
                horario_s = re.split('[A-Za-zñ\.]+',horario_s.lower())   
                for i in horario_s:
                    if i == '':
                        horario_s.remove('')
                    elif i == ' ':
                        horario_s.remove(' ')
                #print('Schedule Hoarios:',horario_s)
                #print(schedule)

                schedule_words = get_schedule.schedule_in_list(schedule,schedule_pattern_words)
                schedule_numbers = get_schedule.schedule_in_list(schedule, schedule_pattern_numbers)
                #print(schedule_words)
                #print(schedule_numbers)
                if len(schedule_numbers) == len(schedule_words):
                    horario = list(zip(schedule_words,schedule_numbers))
                    horario_data = []
                    for hora in horario:
                        hora_box = []
                        for i in hora:
                            
                            hora_box.append(i)
                        hora_box = ' '.join(hora_box)
                        horario_data.append(hora_box)
                    if schedule_numbers:
                        fp = schedule_numbers[0]
                        lp = schedule_numbers[-1]
                    elif schedule_numbers == [] and 'Hoy' in schedule_words:
                        fp = '{}/{}'.format(dia,mes)
                        lp = '{}/{}'.format(dia,mes)
                    from_date = '{}/{}'.format(fp,year)
                    to_date = '{}/{}'.format(lp,year)
                    fp = datetime.strptime(from_date,'%d/%m/%Y').strftime('%d %b')
                    lp = datetime.strptime(to_date,'%d/%m/%Y').strftime('%d %b')
                    fp = get_schedule.transform_to_adv_eng_spa(fp)
                    lp = get_schedule.transform_to_adv_eng_spa(lp)

                    horario = list(zip(horario,horario_s))
                    horario = [' '.join(h) if type(h) is tuple else get_schedule.remove_blank_spaces(h).replace(' ', ' - ') for x in horario for h in x]
                    print(horario)
                    horario_box = []
                    for i,j in zip(horario[::2],horario[1::2]):
                        horario_box.append(' '.join([i,j]))
                    horario = '  /  '.join(horario_box)
                #print(schedule_words,schedule_numbers)
                
                    yield { 
                        'From':from_date,
                        'To':to_date,
                        #'Desde':fp,
                        #'Hasta':lp,
                        'title/Product_name': title[idx].capitalize(),
                        'Place_name/address':'Cines Verdi',
                        'Categoria' : category[idx],
                        'Title_category':main_category,
                        'Nº Category': id_category,
                        'image':image_name,
                        'Hours':horario,
                        'Link_to_buy': 'https://www.onlinecinematickets.com/?p=&s=VERDIMAD&err=Sesi%F3n+expirada+o+suspendida.',
                        'Description':description,
                        #'Area': 'Chamberi ',
                        'City': 'Madrid',
                        'Province': 'Madrid',
                        'Country':'España',
                        'latitud':'',
                        'longitud':'',
                        'Link':'https://madrid.cines-verdi.com/cartelera'
                    }
                else:
                    hoy = '{}/{}'.format(dia,mes)
                    schedule_numbers.insert(0,hoy)
                    #print('Schedule Numbers M:',schedule_numbers)
                    horario = list(zip(schedule_words,schedule_numbers))
                    fp = schedule_numbers[0]
                    lp = schedule_numbers[-1]
                    from_date = '{}/{}'.format(fp,year)
                    to_date = '{}/{}'.format(lp,year)
                    fp = datetime.strptime(from_date,'%d/%m/%Y').strftime('%d %b')
                    lp = datetime.strptime(to_date,'%d/%m/%Y').strftime('%d %b')
                    fp = get_schedule.transform_to_adv_eng_spa(fp)
                    lp = get_schedule.transform_to_adv_eng_spa(lp)

                    horario = list(zip(schedule_words,schedule_numbers))
                    horario_data = []
                    for hora in horario:
                        hora_box = []
                        for i in hora:
                            
                            hora_box.append(i)
                        hora_box = ' '.join(hora_box)
                        horario_data.append(hora_box)

                    horario = list(zip(horario,horario_s))
                    horario = [' '.join(h) if type(h) is tuple else get_schedule.remove_blank_spaces(h).replace(' ', ' - ') for x in horario for h in x]
                    print(horario)
                    horario_box = []
                    for i,j in zip(horario[::2],horario[1::2]):
                        horario_box.append(' '.join([i,j]))
                    horario = '  /  '.join(horario_box)

                    yield { 
                        'From':from_date,
                        'To':to_date,
                        #'Desde':fp,
                        #'Hasta':lp,
                        'Place_name/address':'Cines Verdi',
                        'title/Product_name': title[idx],
                        'Categoria' : category[idx],
                        'Title_category':main_category,
                        'Nº Category': id_category,
                        'image':image_name,
                        'Hours':horario,
                        'Link_to_buy': 'https://www.onlinecinematickets.com/?p=&s=VERDIMAD&err=Sesi%F3n+expirada+o+suspendida.',
                        'Description':description,
                        #'Area': 'Chamberi ',
                        'City': 'Madrid',
                        'Province': 'Madrid',
                        'Country':'España',
                        'latitud':'404.365.832',
                        'longitud':'-37.040.072',
                        'Link': 'https://madrid.cines-verdi.com/cartelera'
                    }

            except Exception as ex:
                print(ex)
                traceback.print_exc()
                pass

       