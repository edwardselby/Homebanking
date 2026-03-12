from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "homebanking"
    app_name: str = "Homebanking API"

    model_config = {"env_prefix": "HB_"}


settings = Settings()
