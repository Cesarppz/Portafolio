#!/home/cesarppz/anaconda3/envs/ws/bin/python3
import re 
import pandas as pd
import argparse
import os
import shutil
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Verifier')

pattern_image_jpg = re.compile(r'(.*).(jpeg|JPG)')
pattern_image_png = re.compile(r'.*.png')

day = datetime.now().day
month = datetime.now().month


def move_missing_images(box_images_faltantes_carpeta,args):
    #Mover las imagenes faltantes que sean jpg
    for i in box_images_faltantes_carpeta:
        if re.match(pattern_image_jpg,i):
            shutil.copy('{}/{}'.format(args.original_image,i),args.image_file)


def _get_path(path):
    if '/' not in path:
        path = '//mnt/c/Users/cesar/Desktop/fiver_javier/{}'.format(path) 
    return path


def move_missing_images_png(box_images_faltantes_carpeta,args):
    #Mov er las imagenes png que son las que no se comprimen bien en photoshop
    for i in box_images_faltantes_carpeta:
        if re.match(pattern_image_png,i):
            shutil.copy('{}/{}'.format(args.original_image,i),args.image_file)


def get_patter(x_list, pattern ):
    original_format = []
    box_changed_frormat = []
    for i in x_list:
        try:
            result = re.match(pattern,i)
            original_format.append(result.group(2)) 
            box_changed_frormat.append(result.group(1))
        except:
            pass
    return box_changed_frormat, original_format


def rename_jpeg(images_list,df):
    list_with_out_format, original_format = get_patter(df['image'],pattern_image_jpg)
    #print(list_with_out_format)
    list_df = df['image'].values
    for idx_format, i in enumerate(list_with_out_format):
        image_name_changed = i+'.jpg'
        original_image_name = i + '.' +original_format[idx_format]
        #original_image_name = i+'.jpeg'

        if (image_name_changed in images_list and original_image_name in list_df) :
            df['image'][df['image'] == original_image_name] = image_name_changed
    return df



def main(args):
    args.file = _get_path(args.file)
    args.image_file = _get_path(args.image_file) 
    args.original_image = _get_path(args.original_image)


    logger.info('Reading the file {}'.format(args.file))
    
    df = pd.read_excel(args.file)
    list_images_in_df = df['image'].values
    images_list = os.listdir(args.image_file)
    
    box_images_faltantes_carpeta = []
    for i in list_images_in_df:
        if i not in images_list:
            box_images_faltantes_carpeta.append(i)
    #print(box_images_faltantes_carpeta)

    logger.info("There are a total of {} unassigned images".format(len(box_images_faltantes_carpeta)))
    logger.info('renaming images with jpeg ending')
    df = rename_jpeg(images_list,df)
    logger.info('Moving png images')
    move_missing_images_png(box_images_faltantes_carpeta,args)
    logger.info('Moving the remaining images')
    move_missing_images(box_images_faltantes_carpeta,args)
    new_path = '{}/{}.xlsx'.format(os.path.dirname(args.file),'results_m_{}_{}'.format(day,month))

    list_images_in_df = df['image'].values
    images_list = os.listdir(args.image_file)
    
    box_images_faltantes_carpeta = []
    for i in list_images_in_df:
        if i not in images_list:
            box_images_faltantes_carpeta.append(i)
    
    if len(box_images_faltantes_carpeta) == 0:
        logger.info('The new file is {}'.format(new_path))
        df.to_excel(new_path)
    else:
        logger.error('These images do not match:\n{}'.format(box_images_faltantes_carpeta))
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_file','-if',type=str,help='Ruta de la carpeta con las imagenes modificadas',default='//mnt/c/Users/cesar/Desktop/fiver_javier/image_500_500/JPEG')
    parser.add_argument('--original_image','-oi',type=str,default='images_{}_{}'.format(day,month),help='Ruta de las imagenes sin modificar')
    parser.add_argument('--file','-f',default='results_{}_{}_.xlsx'.format(day,month),type=str,help='Ruta del archivo de excel')
    args = parser.parse_args()
    main(args)