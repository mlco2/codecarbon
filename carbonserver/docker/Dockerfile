# Dockerfile

# Use Ubuntu to install 3 versions of Python for testing
# For production, you could use python:3.8-slim
FROM ubuntu:20.04

# set work directory
WORKDIR /carbonserver

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt-get update && apt-get upgrade -y && \
 apt-get install -y software-properties-common && \
 add-apt-repository ppa:deadsnakes/ppa -y && \
 apt-get update && \
 apt-get install -y gcc libpq-dev python3.7 python3.6 python3-pip

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY docker/entrypoint.sh /opt
RUN chmod a+x /opt/entrypoint.sh
# copy project
COPY . .
EXPOSE 8000
ENTRYPOINT ["/opt/entrypoint.sh"]
