import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'matute-guide-dev-secret-change-me'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'matute-guide-jwt-dev-secret'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'matute.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    # Cookies httpOnly para web + Bearer header para SPA/Flutter
    JWT_TOKEN_LOCATION = ['cookies', 'headers']
    JWT_ACCESS_COOKIE_NAME = 'mg_access'
    JWT_REFRESH_COOKIE_NAME = 'mg_refresh'
    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_REFRESH_COOKIE_PATH = '/auth'  # solo enviada al endpoint de refresh
    JWT_COOKIE_SECURE = False  # en prod debe ser True (override en ConfigProduccion)
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_CSRF_PROTECT = False  # CSRF mitigado por SameSite + sesión Flask

    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT = '300 per hour'

    APP_VERSION = '1.0.0'


class ConfigDesarrollo(Config):
    DEBUG = True
    ENV = 'development'


class ConfigPruebas(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ConfigProduccion(Config):
    DEBUG = False
    ENV = 'production'
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True


config = {
    'desarrollo': ConfigDesarrollo,
    'pruebas': ConfigPruebas,
    'produccion': ConfigProduccion,
    'default': ConfigDesarrollo,
}
