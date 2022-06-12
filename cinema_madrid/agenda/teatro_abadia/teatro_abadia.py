from os import write
import requests
from bs4 import BeautifulSoup
import re
import urllib
import pandas as pd
from agenda_tools import get_schedule, get_category, download_images, get_category,download_images, months
from datetime import datetime
pattern = re.compile(r'.*(www.teatroabadia.com/es/temporada).*')
url = 'https://www.teatroabadia.com/es/home/'

day = datetime.now().day
mes = datetime.now().month
year = datetime.now().year

link_image_pattern = re.compile(r'^(https?).*/(.+\.(jpg|jpeg|png))')
pattern_schedule = re.compile(r'\d+\s?d?e?\s?([A-Za-záéíóú]+)?')

dict_adv = months.dict_of_months_adv_spanish_to_spanish
dict_eng_spa = months.dict_of_months_adv_spanish_to_english


def write_df(df):
    df.to_csv('results_teatro_abadia_{}_{}.csv'.format(day,mes),index=False)


def make_df(final_list):
    for idx, i in enumerate(final_list):
        n = 0
        try:
            final_list[idx] = pd.DataFrame(i)
        except ValueError as e:
            final_list[idx] = pd.DataFrame.from_dict(i,orient='index').transpose()
    final_df = pd.concat(final_list)
    return final_df


def process(links):
    final_list = []
    for idx, i in enumerate(links):
        print(f'scraping {idx+1}/{len(links)}')
        r = requests.get(i)
        s = BeautifulSoup(r.text,'lxml')
        
        try:
            title = s.find('div',attrs={'class':'otros_datos'}).find('h2').get_text().strip()
        except Exception as e:
            print(e)
        # Hourss - schedule
        try:
            horarios = s.find('div',attrs={'class':'datos_calendario'}).get_text().strip().split('\n')

            for _ in range(len(horarios)):
                try:
                    horarios.remove('')
                except Exception:
                    pass
            if horarios:
                schedule = horarios[1].strip()
                horario = horarios[-1].strip()
            else:
                schedule = None
                horario = None
                
        except Exception as e:
            print(e)

        #description
        try:
            description = s.find('div',attrs={'class':"bloque_texto"}).find('p').text
        except Exception as e:
            print(e)
        #buy link
        try:
            buy_link = s.find('div',attrs={'class':'venta_online'}).find('a').get('href')
        except Exception as e:
            print(e)
        
        try:
            image = s.find('div',attrs={'class':'foto_principal'}).find('img').get('src')
            if image:
                image_name = download_images.download(image,idx=idx+1,len_links=(len(links)),nombre_del_lugar='teatro_abadia')
                print(image_name)
    #             image_name = re.match(link_image_pattern, image).group(2)
    #             urllib.request.urlretrieve(image,image_name)
    #         else:
                #image_name = 'No se encontró una foto'
        except Exception as e:
            print(e)
        
        
        #schedule
        try:
            schedule = schedule.strip().split('al')
        
            if len(schedule) == 1:
                schedule = schedule[0].split('y')

            schedule[0] = schedule[0].replace('\xa0',' ')
            schedule[1] = schedule[1].replace('\xa0',' ')
            fp = re.search(pattern_schedule,schedule[0].strip()).group(0).replace('de','').replace('  ',' ').strip()
            lp = re.search(pattern_schedule,schedule[1].strip()).group(0).replace('de','').replace('  ',' ').strip()
            if len(fp) <= 2:
                fp = f'{fp} {lp.split()[-1]}'
                
            fp = get_schedule.transform_to_adv(fp)
            lp = get_schedule.transform_to_adv(lp)
            fp_from = get_schedule.transform_to_adv_spa_eng(fp)
            lp_to = get_schedule.transform_to_adv_spa_eng(lp)
            fp_from = datetime.strptime(f'{fp_from} {year}','%d %b %Y').strftime('%d/%m/%Y')
            lp_to = datetime.strptime(f'{lp_to} {year}','%d %b %Y').strftime('%d/%m/%Y')

        except Exception as e:
            print(e)
            fp = None
            lp = None
            fp_from = None
            lp_to = None
        
        #Category 
        category = 'Teatro'
        category_id = get_category.id_category(category)
        main_category = get_category.main_category(category)


        #Horario 
        if horario:
            horario = get_schedule.remove_blank_spaces('  /  '.join(horario.split(',')).replace('h','h '))
        else:
            horario = ''
        print(horario)
        
        data_dict = {
            'From':fp_from,
            'To':lp_to,
            # 'Desde':fp,
            # 'Hasta':lp,
            'title/Product_name':title,
            'Place_name/address':'Teatro Abadia',
            'Categoria':'Teatro',
            'Title_category':main_category,
            'Nº Category': category_id,
            'image':image_name,
            'Hours':horario,
            'Link_to_buy':buy_link,
            'Description':description,
            #'Area': 'Chamberi ',
            'City': 'Madrid',
            'Province': 'Madrid',
            'Country':'España',
		    'latitud':'404.353.022',
		    'longitud':'-37.094.283',
            'Link':i
            
        }
        final_list.append(data_dict)
    return final_list


def main():
    r = requests.get(url)
    s = BeautifulSoup(r.text,'lxml')
    lista_cruda = s.find_all('div',attrs={"class":"row montse"})
    lista_cruda = [i.find_all('a') for i in lista_cruda]

    data = []
    for i in lista_cruda:
        for j in i:
            link = j.get('href')
            data.append(link)
    links = set(data)
    links = list(links)

    clean_links = []
    for i in links:
        if re.match(pattern, i):
            clean_links.append(i)

    links = clean_links

    data_finalized = process(links)
    df = make_df(data_finalized)
    write_df(df)

if __name__ == '__main__':
    main()