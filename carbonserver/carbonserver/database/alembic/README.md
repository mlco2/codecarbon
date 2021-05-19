# How to manage the API database

We use Alembic with SQL Alchemy for database (DB) management.

https://www.kimsereylam.com/sqlalchemy/2019/10/18/get-started-with-alembic.html

https://alembic.sqlalchemy.org/en/latest/tutorial.html#the-migration-environment


## Configure the database

Put the url of the database in rhe config file:

For SQLite:
```
sqlalchemy.url = sqlite:///./code_carbon.db
```

For Postgres:
```
sqlalchemy.url = postgresql://codecarbon-user:supersecret@localhost:5480/codecarbon_db
```

# Init the DB
```
alembic upgrade head
```

# Get infos
```
alembic current
```

```
alembic history --verbose
```

Test :
```
cd codecarbon/carbonserver/carbonserver/database
alembic upgrade head --sql
```

# Rollback
```
alembic downgrade base
```


