FROM python:3.8@sha256:d411270700143fa2683cc8264d9fa5d3279fd3b6afff62ae81ea2f9d070e390c
WORKDIR /opt

WORKDIR /opt/codecarbon
# Tips: relative path is from root project folder as we use context in docker-compose
#COPY ./docker/.env.docker .env
COPY setup.py .
RUN python3 setup.py install
COPY . .
# TODO: install codecarbon package?