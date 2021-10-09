from datetime import datetime
change_day = 4


def read_number(path):
    with open(path,'r+') as f:
        code = int(f.read())
        return code


def check_week(path):
    number = read_number(path)
    response = number % 2
    today = datetime.now().weekday()
    if today == change_day:
        new_number = number + 1
        write_number(new_number)
    if response == 1:
        return True
    return False



def write_number(number):
    with open('radical_week.txt','w') as f:
        f.writelines(str(number))
