# import configparser
# import pathlib

# file_config = pathlib.Path(__file__).parent.joinpath("config.ini")
# config = configparser.ConfigParser()
# config.read(file_config)

# HASH_ALGORITHM = config.get("AUTH", "HASH_ALGORITHM", fallback="HS256")
# HASH_SECRET = config.get("AUTH", "HASH_SECRET")
# DB_NAME = config.get("DB", "DB_NAME", fallback="db")

# CLD_NAME = config.get("CLOUDINARY", "CLD_NAME")
# CLD_API_KEY = config.get("CLOUDINARY", "CLD_API_KEY")
# CLD_API_SECRET = config.get("CLOUDINARY", "CLD_API_SECRET")


from pydantic_settings import BaseSettings
from pydantic import SecretStr
from pathlib import Path


class Settings(BaseSettings):
    DB_NAME: str
    DB_URL: str
    HASH_ALGORITHM: str = "HS256"
    HASH_SECRET: str
    CLD_NAME: str
    CLD_API_KEY: str
    CLD_API_SECRET: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: str
    MAIL_PORT: int = 2525
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Contacts App"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"


settings = Settings()
