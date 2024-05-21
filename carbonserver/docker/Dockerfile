# Dockerfile

# Use Ubuntu to install 3 versions of Python for testing
# For production, you could use python:3.8-slim
FROM ubuntu:22.04

# set work directory
WORKDIR /carbonserver

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Prevent apt to ask for region
ENV DEBIAN_FRONTEND noninteractive

# install dependencies
RUN apt-get update && apt-get upgrade -y && \
 apt-get install -y software-properties-common && \
 add-apt-repository ppa:deadsnakes/ppa -y && \
 apt-get update && \
 apt-get install -y gcc libpq-dev python3.11 python3-pip

COPY ./requirements/requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY docker/entrypoint.sh /opt
RUN chmod a+x /opt/entrypoint.sh
# copy project
COPY ./carbonserver/* .
EXPOSE 8000
ENTRYPOINT ["/opt/entrypoint.sh"]
