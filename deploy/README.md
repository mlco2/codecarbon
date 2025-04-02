
# Quickstart
```
./deploy/deploy.py wipe # to start over if you already had a running stack
./deploy/deploy.py setup
./deploy/deploy.py start --traefik --fief --codecarbon
```
just press enter to get default settings when asked

Note that this setup should not be used for production.
The traefik settings are especially insecure and expose the dashboard with no protection.

# Details
The helper cli will automate the tasks but a more manyal example would be:
```
cd deploy
cp .env.fief.example .env.fief
cp .env.traefik.example .env.traefik
nano .env.fief .env.traefik
docker network create shared
docker-compose -p traefik -f traefik-compose.yml up -d
docker-compose -p fief -f fief-compose.yml up -d

cd ..
cp deploy/.env.webapp.example ./webapp/.env.development
cp deploy/.env.example .env
nano .env ./webapp/.env.development
docker-compose -p codecarbon -f docker-compose.yml up -d
```

You can then access the app at https://codecarbon.local


# Notes

## rebuilding
To rebuild the images: 
`docker-compose build`


## verification code

When registering a user, you'll need a verification code.
You can find it with:
docker logs -f fief-fief-worker-1

## local backend/frontend

If you want to run the frontend and/or backend locally, you can edit the files in deploy/rules
For the backend, you also need to edit docker-compose.yml to expose the database on local port (uncomment the corresponding lines).

## OS

The docker network setup on macos prevents some features from working properly.
As a workaround, you can run the frontend and backend localy.
