# Dockerfile

# pull the official docker image
FROM python:3.8.10-slim

# set work directory
WORKDIR /carbonserver

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt update && apt install -y gcc libpq-dev
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# copy project
COPY . .
