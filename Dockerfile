#FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10
FROM python:3.10-buster

RUN pip install --upgrade pip

COPY requirements.txt ./

RUN pip install -r requirements.txt
#RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN mkdir app