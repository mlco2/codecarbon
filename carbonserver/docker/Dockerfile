FROM ubuntu:22.04

WORKDIR /carbonserver

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y gcc libpq-dev python3.11 python3-pip

# Copy the requirements file from the project root
COPY ./requirements/requirements-dev.txt /carbonserver/requirements-dev.txt
RUN pip install -r /carbonserver/requirements-dev.txt

COPY ./requirements/requirements-api.txt /carbonserver/requirements-api.txt
RUN pip install -r /carbonserver/requirements-api.txt

COPY ./carbonserver/docker/entrypoint.sh /opt
RUN chmod a+x /opt/entrypoint.sh

# Copy everything from carbonserver directory to the container
COPY carbonserver /carbonserver

EXPOSE 8000
ENTRYPOINT ["/opt/entrypoint.sh"]
