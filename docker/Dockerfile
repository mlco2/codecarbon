FROM python:3.8
WORKDIR /opt

WORKDIR /opt/codecarbon
# Tips: relative path is from root project folder as we use context in docker-compose
#COPY ./docker/.env.docker .env
COPY pyproject.toml .
RUN python3 -m pip install .
COPY . .
# TODO: install codecarbon package?
