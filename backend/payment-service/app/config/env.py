from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "payment-service"
    PORT: int = 8815
    
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 8552
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "rootpassword"
    MYSQL_DATABASE: str = "payment_db"
    
    JWT_SECRET: str = "change_me_to_a_secure_secret"
    JWT_EXPIRE_MINUTES: int = 60
    ACCOUNT_SERVICE_URL: str = "http://account-service:8661"
    TUITION_SERVICE_URL: str = "http://tuition-service:8732"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8940"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
