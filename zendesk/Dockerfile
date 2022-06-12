FROM  python:3.8.13-bullseye
WORKDIR /app
RUN apt-get update
COPY requirements.txt . 
RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir
COPY /app .
CMD tail -f /dev/null
#CMD ["python3","main.py","@args.txt"]