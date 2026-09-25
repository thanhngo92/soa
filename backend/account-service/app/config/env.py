from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "account-service"
    PORT: int = 8661
    
    # MySQL Database Configuration
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 8552
    MYSQL_USER: str = "account_user"
    MYSQL_PASSWORD: str = "account_password"
    MYSQL_DATABASE: str = "account_db"
    
    JWT_SECRET: str = "change_me_to_a_secure_secret"
    JWT_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
