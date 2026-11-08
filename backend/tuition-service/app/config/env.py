from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "tuition-service"
    PORT: int = 8732

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 8552
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "rootpassword"
    MYSQL_DATABASE: str = "tuition_db"

    JWT_SECRET: str = "super_secret_jwt_key_change_in_prod"
    INTERNAL_SERVICE_KEY: str = "super_internal_service_secret_key_2026"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
