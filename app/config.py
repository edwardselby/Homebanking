from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings, populated from environment variables prefixed
    with ``HB_`` (e.g. ``HB_MONGODB_URI``).  In Docker these are set via
    ``docker-compose.yml``; locally the defaults below work out of the box.
    """

    mongodb_uri: str = "mongodb://localhost:27017/?directConnection=true"
    database_name: str = "homebanking"
    app_name: str = "Homebanking API"
    seed_on_startup: bool = False

    model_config = {"env_prefix": "HB_"}


settings = Settings()
