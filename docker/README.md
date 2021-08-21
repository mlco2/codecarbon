# Usage of CodeCarbon with Docker

## Pre-requisis

Clone the project
```sh
git clone https://github.com/mlco2/codecarbon/codecarbon.git
```

Prepare configuration :
```sh
cd codecarbon
cp docker/docker.env .env
```


## Run

```sh
docker-compose up -d
```
This will run :
 - CodeCarbon API on [http://localhost:8008](http://localhost:8008)
 - Postgresql on localhost:5480
 - PGAdmin 4 on [http://localhost:5080](http://localhost:5080) login : *test@test.com* , password : *test* (Dans PGAdmin, use the host *postgres_codecarbon* and port *5432* for in docker network access)
 - Authentification framework (Keycloak) on [http://localhost:8084/auth/admin/master/console/](http://localhost:8084/auth/admin/master/console/) login : *admin* , password : *admin*
 - Mail service (smtp4dev) on [http://localhost:13000](http://localhost:1300) to view mail sended by Keycloack.
 

## Stop

```sh
docker-compose down
```

Postgres database and PGAdmin configuration are saved in separate volumes.

## View logs

```sh
docker logs codecarbon-api_codecarbon_api_1
```

## Execute tests
```sh
docker exec codecarbon-api_codecarbon_api_1 tox
```

## Force build
```sh
docker-compose up --build
```


## Cleaning
Delete all files :
```sh
docker-compose down -v
docker image rm codecarbon-api
```