from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    app_debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://mindecho:mindecho@localhost:5432/mindecho"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # AWS S3
    aws_region: str = "ap-northeast-1"
    aws_s3_bucket: str = "mindecho-media"
    aws_s3_endpoint_url: str | None = None

    # AWS Bedrock
    aws_bedrock_endpoint_url: str | None = None
    aws_bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
