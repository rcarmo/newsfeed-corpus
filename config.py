""" Configuration """

from os import environ
from io import StringIO
from logging import getLogger
from logging.config import dictConfig
from cProfile import Profile
from pstats import Stats

FETCH_INTERVAL = int(environ.get('FETCH_INTERVAL', 3600))
CHECK_INTERVAL = int(environ.get('CHECK_INTERVAL', 900))
MONGO_SERVER = environ.get('MONGO_SERVER', 'localhost:27017')
DATABASE_NAME = environ.get('DATABASE_NAME', 'feeds')
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
FEED_FETCHER = environ.get('FEED_FETCHER', 'tcp://127.0.0.1:4674')
ENTRY_PARSER = environ.get('ENTRY_PARSER', 'tcp://127.0.0.1:4675')
PROFILER = (environ.get('PROFILER', 'true').lower() == "true")

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
        },
        "ram": {
            "class"    : "logging.handlers.MemoryHandler",
            "formatter": "http",
            "level"    : "WARNING",
            "capacity" : 200
        }
    },
    "loggers": {
    },
    "root": {
        "level"   : "DEBUG" if environ.get('DEBUG','True').lower() == 'true' else "INFO",
        "handlers": ["console"]
    }
})

log = getLogger()

log.info("Configuration loaded.")
