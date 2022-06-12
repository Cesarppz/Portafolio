#encoding=utf-8
import re
import logging
import datetime as dt
import time
import requests
import csv

from datetime import datetime
from agenda_tools import get_schedule, download_images, get_category, months
from agenda_tools.get_schedule import remove_blank_spaces
from bs4 import BeautifulSoup
from requests_html import HTMLSession
session = HTMLSession()


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year
dict_spa_eng_adv = months.dict_of_months_adv_spanish_to_english 


name = 'cine_golem'
logger = logging.getLogger(name)
start_url = ['https://golem.es/golem/golem-madrid']


def write_csv(data):
    name = f'results_cine_golem_{dia}_{mes}.csv'
    with open(name,'w') as f:
        csv_file = csv.writer(f)
        csv_file.writerow(['From','To','title/Product_name','Place_name/address','Categoria','Title_category','Nº Category','image','Hours','Link_to_buy','Description','City','Province','Country','latitud','longitud','Link'])
        for d in data:
            csv_file.writerow(d)


def get_dates(day_page_list,data_dict,link):
    firt_day = day_page_list[0]
    n_last_day = -1
    last_day = day_page_list[n_last_day]
    
    for idx, _ in enumerate(day_page_list):
        if link in data_dict[firt_day]:
            fp = firt_day
            break
        else:
            firt_day = day_page_list[idx+1]
            
    for idx, _ in enumerate(day_page_list):
        if link in data_dict[last_day]:
            lp = last_day
            break
        else:
            n_last_day -= 1
            last_day = day_page_list[n_last_day]
    return fp, lp


def get_data_dict(links):
    data_dict = {}
    day_page_list = []
    hour_dict = {}
    for link in links:
        r = requests.get(link)
        s = BeautifulSoup(r.text,'lxml')
        
        #Extraer los links de la pagina
        links_for_page = ["https://golem.es/{}".format(i.get('href')) for i in s.find('table',attrs={'class',"tabContenido"}).find_all('a',attrs={'class',"txtNegXXL m5"})]
        
        #Extarer la fecha
        day_page = s.find('td',attrs={'class',"tabDia"}).span
        if day_page == None:
            day_page = s.find('td',attrs={'class',"tabDia"}).a
        day_page = day_page.text.strip()
        date_page = re.search(re.compile(r'\d+/\d+/\d+'),day_page).group(0)
        day_page_list.append(date_page)
        day_page = get_schedule.remove_blank_spaces(re.split('\d',day_page)[0])
        
        data_dict[date_page] = links_for_page
        
        response_session = session.get(link).html
        for idx,link_p in enumerate(links_for_page):
            hour_for_link = response_session.xpath(f'//table[@width="100%"][@cellspacing="1"][{idx+1}]//td/table[@cellspacing="0"][@cellpadding="0"][@border="0"]//tr/td//span[@class="horaXXXL"]/a/text()')
            try:
                hour_per_link = hour_dict[link_p]
                hour_per_link.append('{} : {}'.format(day_page,' - '.join(hour_for_link)))
                hour_dict[link_p] = hour_per_link
            except KeyError:
                hour_dict[link_p] = ['{} : {}'.format(day_page,' - '.join(hour_for_link))]

    return data_dict, day_page_list, hour_dict


def get_info(all_data,day_page_list,data_dict,hour_dict):
    data_extracted = []
    for idx, link_page in enumerate(all_data):
        r = requests.get(link_page)
        s = BeautifulSoup(r.text,'lxml')
        response_session = session.get(link_page).html
        
        logger.info(f'Scraping link {idx+1}/{len(all_data)}')
        #schedule
        date = get_dates(day_page_list,data_dict,link_page)
        #title
        name = s.find_all('em',attrs={'class',"txtNegXXXL"})[-1].text.strip()
        #image
        image = 'https://golem.es/{}'.format(response_session.xpath('//table//td[@align="center"]/img/@src')[0])
        print(image)
        image_name = download_images.download_image_with_requests(image,idx=idx, len_links=len(all_data), nombre_del_lugar='cine_golem')
        #hour
        hour = '  /  '.join(hour_dict[link_page])
        #catgory
        if '(V.O.S.E.)' in name:
            category = 'Cine V.O.'
        else:
            category = 'Cine'
        id_category = get_category.id_category(category)
        main_category = get_category.main_category(category)

        description = response_session.xpath('//tr[contains(.,"Sinopsis:")]/following-sibling::tr//text()')[:3]
        description = get_schedule.remove_blank_spaces(' '.join(description).strip())

        result =  [
            date[0], 
            date[1], 
            name.capitalize(),
            'Cine Golem',
            category,
            main_category,
            id_category,
            image_name,
            hour,
            link_page,
            description,
            'Madrid',
            'Madrid',
            'España',
            '4.042.467.509.999.990',
            '-37.135.633',
            link_page
        ]

        if result not in data_extracted:
            data_extracted.append(result)
        else:
            pass
    return data_extracted

def main():
    r = requests.get(start_url[0])
    s = BeautifulSoup(r.text,'lxml')

    next_page_links = ['https://golem.es/{}'.format(i.a.get('href')) for i in s.find_all('td',attrs={'class',"tabNoDia"})]
    links = start_url + next_page_links
    data_dict, day_page_list, hour_dict = get_data_dict(links)

    all_data = []
    for i in data_dict.values():
        all_data.extend(i)
    all_data = list(set(all_data))
    data_extracted = get_info(all_data,day_page_list,data_dict,hour_dict)
    write_csv(data_extracted)


if __name__ == '__main__':
    main()