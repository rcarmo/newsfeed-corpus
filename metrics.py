#!/bin/env python3

""" Metrics agent """

from config import (BIND_ADDRESS, DATABASE_NAME, DEBUG, HTTP_PORT,
                    MONGO_SERVER, METRICS_INTERVAL, log)
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
    """Get database metrics pertaining to feeds"""

    metrics = {
        "database_feeds_count_total": await db.feeds.count(),
        "database_feeds_error_total": 0,
        "database_feeds_unreachable_total": 0,
        "database_feeds_inaccessible_total": 0,
        "database_feeds_redirected_total": 0,
        "database_feeds_fetched_total": 0,
        "database_feeds_pending_total": 0,
    }
    cursor = db.feeds.aggregate([{"$group": {"_id": "$last_status", "count": {"$sum": 1}}}, 
                                 {"$sort":{"count":-1}}])
    counts = {i['_id']: i['count'] async for i in cursor}
    log.debug(counts)
    for k,v in counts.items():
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


async def database_entries(db):
    """Get database metrics pertaining to entries"""

    metrics = {
        "database_entries_count_total": await db.entries.count(),
        "database_entries_lang_en_total": 0,
        "database_entries_lang_pt_total": 0,
        "database_entries_lang_other_total": 0
    }
    cursor = db.entries.aggregate([{"$group": {"_id": "$lang", "count": {"$sum": 1}}}, 
                                   {"$sort":{"count":-1}}])
    counts = {i['_id']: i['count'] async for i in cursor}})
    for k, v in counts.items():
        if k in ['en', 'pt']:
            metrics['database_entries_lang_' + k + '_total'] += v
        else
            metrics['database_entries_lang_other_total'] += v
    return metrics


def tree_split(flat, drop_last=0):
    res = {}
    for k, v in flat.items():
        parts = k.split('_').pop(-1-drop_last)
        branch = res
        for part in parts[:-1]:
            branch = branch.setdefault(part, {})
        branch[parts[-1]] = v
    return res


async def monitor_loop():
    redis = await connect_redis()
    while True:
        metrics.update(await database_feeds())
        metrics.update(await database_entries())
        tree = tree_split(metrics, drop_last=1)
        log.debug(tree)
        await publish(queue, 'ui', {'event': 'metrics_feeds', 'data': tree['database']['feeds']})
        await publish(queue, 'ui', {'event': 'metrics_entries', 'data': tree['database']['entries']})
        await redis.mset({'metrics:' + k:v for k,v in metrics.items()})
        await sleep(CHECK_INTERVAL)
    redis.close()
    await redis.wait_closed()


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
