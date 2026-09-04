from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "jewel"
    mongo_timeout_ms: int = 100
    default_currency: str = "USD"
    candidate_cap: int = 200


settings = Settings()
