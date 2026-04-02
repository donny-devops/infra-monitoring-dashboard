import os


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
    METRIC_RETENTION_DAYS = int(os.environ.get("METRIC_RETENTION_DAYS", 90))
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


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
