from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    toxiproxy_url: str
    prometheus_url: str
    target_url: str

    class Config:
        env_file = ".env"


settings = Settings()