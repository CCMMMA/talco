FROM python:3.10

WORKDIR /aiquam

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app/ app/
COPY app.py .
COPY config.py .
COPY .flaskenv .
COPY run.sh .
RUN chmod u+x run.sh

ENTRYPOINT ["./run.sh"]