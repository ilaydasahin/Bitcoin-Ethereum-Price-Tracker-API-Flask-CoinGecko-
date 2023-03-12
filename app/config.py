import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'crypto-tracker-dev-key')
    COINGECKO_BASE_URL = os.environ.get('COINGECKO_BASE_URL', 'https://api.coingecko.com/api/v3')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 60))
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 10))

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    CACHE_DEFAULT_TIMEOUT = 0

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
