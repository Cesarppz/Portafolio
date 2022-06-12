#!/home/cesarppz/anaconda3/envs/ws/bin/python3
import pandas as pd
import os
import re
import subprocess
import glob
import shutil
from datetime import datetime
import traceback
from agenda_tools import get_title, get_schedule
dia = datetime.now().day
mes = datetime.now().month

patter_csv = re.compile(r'results_.*.csv')


def drop_nan_in_the_df(df,columns= ['image']):
    df = df.dropna(subset=columns)
    return df


def rm_dataframes(files,path):
    for i in files:
        subprocess.run(['rm','{}/{}'.format(path,i)])


def write_df(df, path, format_file= 'xlsx'):
    if format_file == 'xlsx':
        df.to_excel('{}/results_{}_{}_.{}'.format(path,dia,mes,format_file),index=False)


def read_df(files, path , concat=True):
    box = []
    for i in files:
        try:
            box.append(pd.read_csv(f'{path}/{i}'))
        except Exception as ex:
            #traceback.print_exc(ex)
            print(ex,f'Sitio {i}')

    if concat == True:
        return pd.concat(box)
    else:
        return box

def get_csv_file(files):
    box = []
    for i in files:
        if re.match(patter_csv,i):
            box.append(i)
    return box

def concat_dataframes(path_folder = '//mnt/c/Users/cesar/Desktop/fiver_javier'):
    data_sets = os.listdir(path_folder)
    box = get_csv_file(data_sets)
    df = read_df(box, path_folder)
    df = get_title.capitals_titles(df)
#    df = get_schedule.desde_hasta_in_schedule(df)
    df = drop_nan_in_the_df(df)  #Borrar los rows que no tengan imagenes 
    write_df(df , path_folder)
    rm_dataframes(box,path_folder)


def concat_images(path_folder = '//mnt/c/Users/cesar/Desktop/fiver_javier'):
    list_of_data = glob.glob(f'{path_folder}/data_*')
    images_folder_name = f'images_{dia}_{mes}'
    if images_folder_name not in os.listdir(path_folder): #Si la carpeta no existe la creao
        os.makedirs(f'{path_folder}/{images_folder_name}')
    for li in list_of_data:
        for image in glob.glob(f'{li}/*'):
            shutil.move(image,f'{path_folder}/{images_folder_name}')
        subprocess.run(['rmdir',li])