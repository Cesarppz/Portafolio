from datetime import datetime
from reading import read 
import time as t
import logging 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M')
logger = logging.getLogger('Cron-app')

def check_day(day, today):
    today = today.weekday()
    if type(day) == list:  #Si se colocaron varios dias 
        for d in day:
            if d == today:
                return True
    else:
        if day == today:
            return True
    return False


def check_time(time, today, name):
    today_time = today.time()
    time = datetime.strptime(time,'%H:%M')

    if today_time.hour == time.hour and today_time.minute == time.minute:
        return True
    # Congelar el programa los minutos que falten para que la clse comience

    elif today_time < time.time():
        logger.info(f'Para el chat "{name}" falta para la entrega del mensaje')
        # Si faltan pocos minutos que el programa espere, de lo contrario que se apague 
        rest_minutes = today_time.minute - time.minute
        if today_time.hour - time.hour == 0 and abs(rest_minutes) <= 10:
            rest = today_time.minute - time.minute
            rest = rest * 60
            rest = abs(rest)
            logger.info('Faltan '+str(rest)+' minutos')
            t.sleep(rest)
            return True

    elif today_time > time.time():
        logger.info(f'Para el chat "{name}" la hora de entrega ya pasó')
        # Si faltan pocos minutos que el programa espere, de lo contrario que se apague 
        rest_minutes = today_time.minute - time.minute
        if today_time.hour - time.hour == 0 and abs(rest_minutes) <= 10:
            delay = today_time.minute - time.minute
            logger.info('Tienes un retraso de: '+str(delay)+' minutos')
            return True

    else:
        logger.info(f'Para el chat "{name}" la hora de entrega no es cercana')
        return False


def check_date(destination,path):
    if destination == 'G':
        destination = 'groups'
    elif destination == 'P':
        destination = 'persons'
    # Inicializo la fecha actual
    today = datetime.now()
    #Traigo los datos 
    data = read(path)
    data_names = data[destination]
    data_of_the_day = []

    for name, value in data_names.items():
        day = check_day(value[1][1], today)
        if day == True:
            tiempo = check_time(value[1][0], today, name)
            if tiempo == True:
                data_of_the_day.append(name)
    
    return data_of_the_day

