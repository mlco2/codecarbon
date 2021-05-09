# Testing the carbon server 


## Behaviors to test :


### Domain logic
To test the interface exposed by entities, in memory repositories can be used to isolate the domain logic from technical implementation.
Current entities tests are located in tests/infra/repositories


### Infrastructure
- Test the technical components on which the logic relies 
- Spawn a local Database : use docker / alembic to generate and populate
- Http server setup in api/tests
- Authentication / user management  

### Routers 
- To test a router, validation parameters are ensured by pydantic, and logic is tested by interfaces.
We want to test different responses so clients can be informed of the handling of their request, and adapt it if necessary.

### Integration
- Database : in the CI, a prod-like database can be used to test features on real data
- Code Carbon package : Launch a train scenario


## Running the tests :

Create a virtual environment

### Install the test setup 

git clone
cd carbonserver
python -m setup install
python -m setup build   # Verify the build on local environement
pip install -rrequirements-test.txt # Install test dependencies



### Run tests
tox -e api # Unit tests on api
tox -e integration # Integration tests (needs database automated setup)



To test the HTTP layer, you can also deploy a local instance :

cd carbonserver/
uvicorn main:app

Swagger documentation is available at localhost:8000/docs.
Collection of example requests could be stored in carbonserver/collections to test with Postman-like tooling.
