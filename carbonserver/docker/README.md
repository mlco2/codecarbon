# Run Code Carbon API with Docker

This is to start using `docker-compose` to run the carbonserver app.

* Run the carbonserver app with `docker-compose`
* Switch between sqlite or postgres (comment/uncomment in `docker-compose.yml` the database)
```yaml
    environment:
      # DATABASE_URL: sqlite:///./code_carbon.db
      DATABASE_URL: postgresql://${DATABASE_USER:-codecarbon-user}:${DATABASE_PASS:-supersecret}@postgres/${DATABASE_NAME:-codecarbon_db}
```

> Access the app on port `8008` instead of default `8000`, see `ports` in `docker-compose.yml`.
