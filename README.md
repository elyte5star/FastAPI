API with FastAPI.

## Project Setup

 - Clone project with

  ```
  git clone git@github.com:elyte5star/FastAPI.git
  ```
  - Create file .env and set values for the environment variables below:

  ```
    LOG_LEVEL="INFO"
    API_ALGORITHM="HS256"
    API_CORS_ORIGINS='["https://frontend.elyte.com", "https://elyte.com", "http://elyte.com", "http://*.elyte.com", "http://localhost", "http://elyte.com:8080", "http://elyte.com:3001", "https://localhost", "https://elyte.com:443", "https://elyte.com:4001", "http://localhost:3000"]'
    API_JWT_SECRETKEY="7a3c54660456ff1137b652e498624dfa09a0ec12b4fc49d38b85465da15027a
    API_JWT_TOKEN_EXPIRE_MINUTES="60"
    API_JWT_REFRESH_TOKEN_EXPIRE_MINUTES="43200"
    RQ_URL="amqp://rabbitUser:elyteRQ@localhost:5672/"
    DB_URL="postgresql+asyncpg://userExample:54321@localhost/elyte"
    CLIENT_URL="*"
    LOG_PATH="./api.log"
    MICROSOFT_CLIENT_ID="*******"
    MICROSOFT_TENANT_ID="*****"
    MICROSOFT_CLIENT_SECRET="**"
    GOOGLE_CLIENT_ID="******'''"
    GOOGLE_CLIENT_SECRET=""****"

    
    
  ```
  ```

- Install dependencies: use poetry install

```

```
- Expose the application to POSTGRES Database at port 5432
- Expose the application to RabbitMQ at port 5672

```
```
- Run the Application:  fastapi dev main.py

```
 