#!/bin/env python3

""" Web server """

from config import (BIND_ADDRESS, DATABASE_NAME, DEBUG, HTTP_PORT,
                    MONGO_SERVER, log)
from datetime import datetime
from functools import lru_cache
from multiprocessing import cpu_count

from aiocache import SimpleMemoryCache, cached
from common import REDIS_NAMESPACE, connect_redis
from mako.template import Template
from motor.motor_asyncio import AsyncIOMotorClient
from sanic import Sanic
from sanic.exceptions import FileNotFound, NotFound
from sanic.response import html, json, text

app = Sanic(__name__)
layout = Template(filename='views/layout.tpl')

redis = None
db = None


@app.route('/', methods=['GET'])
async def homepage(req):
    """Main page"""
    return html(layout.render(timestr=datetime.now().strftime("%H:%M:%S.%f")))


@app.route('/test', methods=['GET'])
async def get_name(req):
    """Endpoint for front-end load testing using wrk.
       Reference measurement: 25K requests/s on 4 cores of a 2.9GHz i5"""
    return text("test")


@app.route('/status', methods=['GET'])
async def get_status(req):
    """Status endpoint for the web UI - will expose all counters."""

    return json({
        "feed_count": await redis.hget(REDIS_NAMESPACE + 'status', 'feed_count'),
        "item_count": await redis.hget(REDIS_NAMESPACE + 'status', 'item_count')
    })


@app.route('/feeds/<order>', methods=['GET'])
@app.route('/feeds/<order>/<last_id>', methods=['GET'])
@cached(ttl=20)
async def get_feeds(req, order, last_id=None):
    """Paged navigation of feeds - experimental, using aiocache to lessen database hits.
       Right now this clocks in at 10K requests/s when using only 2 cores on my i5 Mac."""

    limit = 50
    fields = {'_id': 1, 'title': 1, 'last_fetched': 1, 'last_status': 1}
    if last_id:
        data = await db.feeds.find({last_id < '_id'},
                                   fields).sort(order).limit(limit).to_list(limit)
    else:
        data = await db.feeds.find({},
                                   fields).sort(order).limit(limit).to_list(limit)
    return json(data)

app.static('/', './static')

@app.listener('after_server_start')
def init_connections(sanic, loop):
    """Bind the database and Redis client to Sanic's event loop."""

    global redis, db
    redis = connect_redis()
    motor = AsyncIOMotorClient(MONGO_SERVER, io_loop=loop)
    db = motor[DATABASE_NAME]


if __name__ == '__main__':
    log.debug("Beginning run.")
    app.run(host=BIND_ADDRESS, port=HTTP_PORT, workers=cpu_count(), debug=DEBUG)
