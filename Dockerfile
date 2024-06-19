FROM python:3.10

WORKDIR /talco

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app/ app/
COPY wsgi.py .
COPY config.json .
COPY config.py .
COPY talco.ini .
COPY run.sh .
RUN chmod u+x run.sh

ENTRYPOINT ["./run.sh"]
#ENTRYPOINT ["tail", "-f", "/dev/null"]