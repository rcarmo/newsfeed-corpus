#!/bin/env python3

""" Metrics agent """

from config import (BIND_ADDRESS, DATABASE_NAME, DEBUG, HTTP_PORT,
                    MONGO_SERVER, log)
from datetime import datetime, timedelta
from functools import lru_cache
from multiprocessing import cpu_count

from aiocache import SimpleMemoryCache, cached
from common import REDIS_NAMESPACE, connect_redis, dequeue, subscribe
from mako.template import Template
from motor.motor_asyncio import AsyncIOMotorClient
from sanic import Sanic

from sanic.exceptions import FileNotFound, NotFound
from sanic.response import html, json, text, stream
from sanic.server import HttpProtocol
from ujson import dumps

app = Sanic(__name__)
redis = None
db = None

# Metrics in Prometheus format
metrics = {
    "database_feeds_total": None,
    "database_feeds_error_total": None,
    "database_feeds_unreachable_total": None,
    "database_feeds_inaccessible_total": None,
    "database_feeds_redirected_total": None,
    "database_feeds_fetched_total": None,
    "database_feeds_pending_total": None,
    "database_entries_total": None,
    "database_entries_language_en": None,
    "database_entries_language_pt": None,
    "database_entries_language_other": None,
    "fetcher_requests_total": None,
}

@app.route('/', methods=['GET'])
async def homepage(req):
    """Main page"""
    for 
    return ""


@app.route('/status', methods=['GET'])
async def get_status(req):
    """Status endpoint for the web UI - will expose all counters."""

    return json({
        "feed_count": await redis.hget(REDIS_NAMESPACE + 'status', 'feed_count'),
        "item_count": await redis.hget(REDIS_NAMESPACE + 'status', 'item_count')
    })


async def database_feeds(db):
    cursor = db.feeds.aggregate([{"$group": {"_id": "$last_status", "count": {"$sum": 1}}}, 
                                 {"$sort":{"count":-1}} ])
    counts = {i['_id']: i['count'] async for i in cursor}
    log.debug(counts)
    metrics = {
        "database_feeds_error_total": 0,
        "database_feeds_unreachable_total": 0,
        "database_feeds_inaccessible_total": 0,
        "database_feeds_redirected_total": 0,
        "database_feeds_fetched_total": 0,
        "database_feeds_pending_total": 0,
    }
    for k,v in counts:
        if k==None:
            metrics['database_feeds_pending_total'] += v
        elif k==0:
            metrics['database_feeds_unreachable_total'] += v
        elif 0 < k < 300:
            metrics['database_feeds_fetched_total'] += v
        elif 300 <= k < 400:
            metrics['database_feeds_redirected_total'] += v
        elif 400 <= k < 500:
            metrics['database_feeds_inaccessible_total'] += v
        else:
            metrics['database_feeds_error_total'] += v
    log.debug(metrics)
    return metrics



@app.route('/stats/parser', methods=['GET'])
async def handler(req):
    cursor = db.entries.aggregate([{"$group": {"_id": "$lang", "count": {"$sum": 1}}}, 
                                   {"$sort":{"count":-1}} ])
    return json({'total': await db.entries.count(),
                 'status': {i['_id']: i['count'] async for i in cursor}})

@app.route('/stats/post_times', methods=['GET'])
async def handler(req):
    # TODO: this aggregation is broken
    cursor = db.entries.aggregate([{"$match":{"date":{"$gte": datetime.now() - timedelta(days=7), "$lt": datetime.now()}}},
                                   {"$group":{"_id": {"lang":"$lang", "hour": { "$hour": "$date"}},"count":{"$sum": "$count"}}},
                                   {"$sort":{"hour":1}}])
    

async def monitor_loop():
    while True:

        sleep(5)



@app.listener('after_server_start')
async def init_connections(sanic, loop):
    """Bind the database and Redis client to Sanic's event loop."""

    global redis, db
    redis = await connect_redis()
    motor = AsyncIOMotorClient(MONGO_SERVER, io_loop=loop)
    db = motor[DATABASE_NAME]
    ensure_future(monitor_loop)


if __name__ == '__main__':
    log.debug("Beginning run.")
    app.run(host=BIND_ADDRESS, port=HTTP_PORT, workers=cpu_count(), debug=DEBUG, protocol=CustomHttpProtocol)
