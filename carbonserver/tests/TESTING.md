# Testing the carbon server


## Behaviors to test :


### Domain logic
To test the interface exposed by entities, in memory repositories can be used to isolate the domain logic from technical
 implementation.

### Infrastructure

- Testing SqlRepositories :
    - Spawn a test database :
        - Use docker compose to launch a Postgres instance from project root
        ```bash
        docker compose up -d postgres pgadmin
        ```
        - Use [alembic](carbonserver/carbonserver/database/alembic/README.md) to inject last version of database schema
        ```bash
        alembic upgrade head
        ```

- Http server setup in tests/api (TODO)
- Authentication / user management (TODO)

### Servcies & Use cases

Domain logic can be tested at a higher level, with more complex setups, in service/use cases tests.
Use case tests mocks repositories returns to focus on



### Routers
To test a router, validation parameters are ensured by pydantic (available on the swagger documentation),
and logic is tested by interfaces.
A Postman collection of requests is available: ```carbonserver/tests/postman/TestCollection.postman_collection.json```.



### Integration
- Database : in the CI, a prod-like database can be used to test features on real data (TODO)
- Code Carbon package : Launch a train scenario (TODO)


## Running the tests :

### Install the test setup

In a virtual environment, install and build the api package :
```bash
git clone git@github.com:mlco2/codecarbon.git
git checkout api
cd carbonserver
python -m setup install
python -m setup build   # Verify the build on local environment
pip install -r requirements-test.txt # Install test dependencies
```


### Run tests
```bash
tox -e unit # Unit tests on api
tox -e integration # Integration tests
```


To test the HTTP layer, you can also deploy a local instance :

```bash
cd carbonserver/
uvicorn main:app --reload
```

Swagger documentation is available at http://localhost:8000/docs


### Run locally the CI


To test the full build process, the Github Actions workflow can be executed locally with act ([install available here](https://raw.githubusercontent.com/nektos/act/master/install.sh)):
```bash
# Build patched dockerfile from project root
docker build act -t local/ubuntu-builder:latest

# Run GA job from patched instance
act -j build_server -P ubuntu-latest=local/ubuntu-builder:latest
```
