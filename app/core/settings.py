from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_key: str
    dev_api_key: str
    my_secret_admin_key: str
    max_payload_size_bytes: int = 1048576
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()