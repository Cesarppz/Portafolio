import json
import requests
import argparse
import csv
import logging

from datetime import datetime 
from agenda_tools import get_schedule, download_images, get_category

mes = datetime.now().month
dia = datetime.now().day
year = datetime.now().year

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')

logger = logging.getLogger('Cines_yelmo')

def open_file(path=f'/home/cesar/Downloads/GetNowPlaying_{dia}_{mes}.json'):
    with open(path) as f:
        file = json.loads(f.read())
        return file


def get_data(file):
    all_data = {}
    all_schedule = {}
    all_hours = {}

    for  i in file['d']['Cinemas']:
        if i['Key'] == 'ideal' or  i['Key'] == "palafox-luxury" or i['Key'] == "plaza-norte-2-luxury":
            data = {}
            data_dates = {}
            data_hours = {}
            for idx, d in enumerate(i['Dates']):
                date = (d['ShowtimeDate'])
                for movie in d['Movies']:
                    logger.info("Scraping ...")
                    
                    list_horas = []
                    for h in movie['Formats']:
                        language = (h['Language'])
                        time_list = []
                        for st in h['Showtimes']:
                            time = (st['Time'])
                            time_list.append(time)
                        list_horas.append('{} : {}'.format(language,' - '.join(time_list)))
                        
                    list_horas = '{} : {}'.format(date,' - '.join(list_horas))
                    if movie['Title'] not in list(data_hours.keys()):
                        data_hours[movie['Title']] = [list_horas]
                    else:
                        list_horarios_f = data_hours[movie['Title']]
                        list_horarios_f.append(list_horas)
                        data_hours[movie['Title']] = list_horarios_f
                    #category
                    if language == 'VOSE':
                        category = 'Cine V.O.'
                    else:
                        category = 'Cine'
                        
                    #schedule
                    if movie['Title'] not in list(data_dates.keys()):
                        data_dates[movie['Title']] = [date]
                    else:
                        list_of_dates_movie = data_dates[movie['Title']]
                        list_of_dates_movie.append(date)
                        data_dates[movie['Title']] = list_of_dates_movie
                        
                    #Data
                    image = movie['Poster']
                    id_category = get_category.id_category(category)
                    main_category = get_category.main_category(category)
                    if movie['Title'] not in list(data.keys()):
                        data[movie['Title']] = {
                        'Title':movie['Title'],
                        'Image':image,
                        'Description':movie['Synopsis'],
                        'link':'https://www.yelmocines.es/sinopsis/{}'.format(movie['Key']),
                        'Cine':i['Key'],
                        'Category':category,
                        'categoy_id':id_category,
                        'main_category':main_category}
                        
                    
                    #print([formats for h in movie['Formats'] for formats in h])
            all_data[i['Key']] = data
            all_schedule[i['Key']] = data_dates
            all_hours[i['Key']] = data_hours

    return all_data, all_schedule, all_hours


def merge_data(all_data, all_schedule, all_hours,cines):
    for i in cines:
        for p in all_data[i]:
            fp = '{} {}'.format(all_schedule[i][p][0],year)
            fp = datetime.strptime(get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(fp)),'%d %b %Y').strftime('%d/%m/%Y')
            lp = '{} {}'.format(all_schedule[i][p][-1],year)
            lp = datetime.strptime(get_schedule.transform_to_adv_spa_eng(get_schedule.transform_to_adv(lp)),'%d %b %Y').strftime('%d/%m/%Y')

            hours = '  /  '.join(all_hours[i][p])
            all_data[i][p]['From'] = fp
            all_data[i][p]['to'] = lp
            all_data[i][p]['hours'] = hours
    return all_data


def write_csv(data):
    logger.info('Writing file to csv')
    name = f'results_cines_yelmo_{dia}_{mes}.csv'
    with open(name,'w') as f:
        csv_file = csv.writer(f)
        csv_file.writerow(['From','To','title/Product_name','Place_name/address','Categoria','Title_category','Nº Category','image','Hours','Link_to_buy','Description','City','Province','Country','latitud','longitud','Link'])
        for d in data:
            csv_file.writerow(d)


def prepare_data_for_csv(all_data,cines):
    logger.info("Preparing data for csv file type")
    data_csv = []
    for i in cines:
        if i.lower() == 'ideal':
            latitud = '404.138.233'
            longitud = '-37.037.766'
        elif i.lower() == 'palafox-luxury':
            latitud = '404.300.857'
            longitud = '-37.008.696'
        else:
            latitud = ''
            longitud = ''

        for p in all_data[i]:
            data_csv.append([
                all_data[i][p]['From'],
                all_data[i][p]['to'],
                all_data[i][p]['Title'],
                'Cine {}'.format(i.capitalize()),
                all_data[i][p]['Category'],
                all_data[i][p]['main_category'],
                all_data[i][p]['categoy_id'],
                all_data[i][p]['Image'],
                all_data[i][p]['hours'],
                all_data[i][p]['link'],
                all_data[i][p]['Description'],
                'Madrid',
                'Madrid',
                'España',
                latitud,
                longitud,
                all_data[i][p]['link']
            ])

    return data_csv



def download_images_from_list(data):
    for idx, i in enumerate(data):
        url = i[7]
        logger.info(f'Extracting image {idx+1}/{len(data)}')
        image_name = download_images.download_image_with_requests(url,nombre_del_lugar='cines_yelmo',idx=idx,len_links=len(data))
        i[7] = image_name

    return data


def run(path,cines):
    if path:
        file = open_file(path)
    else:
        file = open_file()
    all_data, all_schedule, all_hours = get_data(file)
    all_data = merge_data(all_data, all_schedule, all_hours, cines)
    data_csv = prepare_data_for_csv(all_data,cines)
    data_csv = download_images_from_list(data_csv)
    write_csv(data_csv)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file','-f',type=str,help='Path del archivo json',nargs='?')
    parser.add_argument('--cines','-c',default=['ideal', 'palafox-luxury', 'plaza-norte-2-luxury'],type=str,help='Los cines que se van a scrapear',nargs='?')
    args = parser.parse_args()
    run(args.file,args.cines)
