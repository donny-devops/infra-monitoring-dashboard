import os


def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than 0")
    return value


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://infra:changeme@localhost:5432/infra_monitoring",
    )
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    AI_ANALYSIS_ENABLED = os.environ.get("AI_ANALYSIS_ENABLED", "true").lower() == "true"
    METRIC_RETENTION_DAYS = _positive_int("METRIC_RETENTION_DAYS", 90)
    SCHEDULER_TIMEZONE = os.environ.get("SCHEDULER_TIMEZONE", "UTC")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://infra:changeme@localhost:5432/infra_monitoring_test",
    )


def assert_production_safe(app_config) -> None:
    """Fail fast when production is pointed at the development secret."""
    secret = app_config.get("SECRET_KEY", "")
    if secret in {"", "dev-secret"}:
        raise RuntimeError("SECRET_KEY must be set to a non-default value in production")


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
