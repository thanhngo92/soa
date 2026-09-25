from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "tuition-service"
    PORT: int = 8732
    
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 8552
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "rootpassword"
    MYSQL_DATABASE: str = "tuition_db"
    
    JWT_SECRET: str = "change_me_to_a_secure_secret"
    JWT_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
