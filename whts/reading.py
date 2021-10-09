import yaml
data = None 


def read(path):
    global data
    if  data == None:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return data
    else:
        return data

