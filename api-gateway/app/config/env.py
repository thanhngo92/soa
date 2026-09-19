from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ACCOUNT_SERVICE_URL: str = "http://account-service:8661"
    TUITION_SERVICE_URL: str = "http://tuition-service:8732"
    PAYMENT_SERVICE_URL: str = "http://payment-service:8815"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8940"
    ALLOWED_ORIGIN: str = "http://localhost:3659"

    class Config:
        env_file = ".env"


settings = Settings()

SERVICE_MAP: dict[str, str] = {
    "accounts":      settings.ACCOUNT_SERVICE_URL,
    "tuitions":      settings.TUITION_SERVICE_URL,
    "payments":      settings.PAYMENT_SERVICE_URL,
    "notifications": settings.NOTIFICATION_SERVICE_URL,
}
