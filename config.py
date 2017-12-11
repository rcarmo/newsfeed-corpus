#!/bin/env python3

""" Configuration """

from cProfile import Profile
from logging import getLogger
from logging.config import dictConfig
from os import environ

FETCH_INTERVAL = int(environ.get('FETCH_INTERVAL', 3600))
CHECK_INTERVAL = int(environ.get('CHECK_INTERVAL', 900))
METRICS_INTERVAL = int(environ.get('METRICS_INTERVAL', 5))
HTTP_PORT = int(environ.get('HTTP_PORT', 8000))
BIND_ADDRESS = environ.get('BIND_ADDRESS','0.0.0.0')
DEBUG = environ.get('DEBUG','False').lower() == 'true'
MAX_CONCURRENT_REQUESTS = int(environ.get('MAX_CONCURRENT_REQUESTS', 100))
MONGO_SERVER = environ.get('MONGO_SERVER', 'localhost:27017')
REDIS_SERVER = environ.get('REDIS_SERVER', 'localhost:6379')
REDIS_NAMESPACE = environ.get('REDIS_NAMESPACE', 'newspipe:')
DATABASE_NAME = environ.get('DATABASE_NAME', 'feeds')
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
PROFILER = environ.get('PROFILER','False').lower() == "true"

if PROFILER:
    profiler = Profile()
    profiler.enable()
else:
    profiler = None

async def get_profile():
    """Return a profile dump"""
    
    global profiler
    log.info(profiler)

    if profiler:
        profiler.create_stats()
        return profiler.stats
    return None


dictConfig({
    "version": 1,
    "formatters": {
        "http": {
            "format" : "localhost - - [%(asctime)s] %(process)d %(levelname)s %(message)s",
            "datefmt": "%Y/%m/%d %H:%M:%S"
        },
        "service": {
            "format" : "%(asctime)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class"    : "logging.StreamHandler",
            "formatter": "service",
            "level"    : "DEBUG",
            "stream"   : "ext://sys.stdout"
        }
    },
    "loggers": {
        "sanic.static": {
            "level"   : "INFO",
            "handlers": ["console"]
        }
    },
    "root": {
        "level"   : "DEBUG" if DEBUG else "INFO",
        "handlers": ["console"]
    }
})

log = getLogger()

log.info("Configuration loaded.")
#for k in sorted(environ.keys()):
#    log.debug("{}={}".format(k,environ[k]))
