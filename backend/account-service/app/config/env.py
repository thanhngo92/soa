from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "account-service"
    PORT: int = 8661
    MONGO_URI: str = "mongodb://mongodb:27017"
    DATABASE_NAME: str = "account_db"
    JWT_SECRET: str = "change_me_to_a_secure_secret"
    JWT_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
