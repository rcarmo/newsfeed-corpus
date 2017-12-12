#!/bin/env python3

""" Metrics agent """

from asyncio import ensure_future, sleep
from config import (BIND_ADDRESS, DATABASE_NAME, DEBUG, HTTP_PORT,
                    METRICS_INTERVAL, MONGO_SERVER, log)
from copy import deepcopy
from datetime import datetime, timedelta
from functools import lru_cache, reduce
from multiprocessing import cpu_count
from time import time

from aiocache import SimpleMemoryCache, cached
from common import REDIS_NAMESPACE, connect_redis, dequeue, publish, subscribe
from mako.template import Template
from motor.motor_asyncio import AsyncIOMotorClient
from sanic import Sanic
from sanic.exceptions import FileNotFound, NotFound
from sanic.response import html, json, stream, text
from sanic.server import HttpProtocol
from ujson import dumps

app = Sanic(__name__)
redis = None
db = None

# Metrics in Prometheus format
metrics = {
    "database_feeds_total": None,
    "database_feeds_status_error_total": None,
    "database_feeds_status_unreachable_total": None,
    "database_feeds_status_inaccessible_total": None,
    "database_feeds_status_redirected_total": None,
    "database_feeds_status_fetched_total": None,
    "database_feeds_status_pending_total": None,
    "database_entries_total": None,
    "database_entries_language_en": None,
    "database_entries_language_pt": None,
    "database_entries_language_other": None,
    "fetcher_requests_total": None,
}

@app.route('/', methods=['GET'])
async def homepage(req):
    """Main page"""
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
        "database_feeds_status_error_total": 0,
        "database_feeds_status_unreachable_total": 0,
        "database_feeds_status_inaccessible_total": 0,
        "database_feeds_status_redirected_total": 0,
        "database_feeds_status_fetched_total": 0,
        "database_feeds_status_pending_total": 0,
    }
    cursor = db.feeds.aggregate([{"$group": {"_id": "$last_status", "count": {"$sum": 1}}}, 
                                 {"$sort":{"count":-1}}])
    counts = {i['_id']: i['count'] async for i in cursor}
    for k,v in counts.items():
        if k==None:
            metrics['database_feeds_status_pending_total'] += v
        elif k==0:
            metrics['database_feeds_status_unreachable_total'] += v
        elif 0 < k < 300:
            metrics['database_feeds_status_fetched_total'] += v
        elif 300 <= k < 400:
            metrics['database_feeds_status_redirected_total'] += v
        elif 400 <= k < 500:
            metrics['database_feeds_status_inaccessible_total'] += v
        else:
            metrics['database_feeds_status_error_total'] += v
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
    counts = {i['_id']: i['count'] async for i in cursor}
    for k, v in counts.items():
        if k in ['en', 'pt']:
            metrics['database_entries_lang_' + k + '_total'] += v
        else:
            metrics['database_entries_lang_other_total'] += v
    return metrics



@app.route('/stats/post_times', methods=['GET'])
async def handler(req):
    # TODO: this aggregation is broken
    cursor = db.entries.aggregate([{"$match":{"date":{"$gte": datetime.now() - timedelta(days=7), "$lt": datetime.now()}}},
                                   {"$group":{"_id": {"lang":"$lang", "hour": { "$hour": "$date"}},"count":{"$sum": "$count"}}},
                                   {"$sort":{"hour":1}}])
    

def tree_split(flat, drop_last=0):

    def merge(a, b):
        if not isinstance(b, dict):
            return b
        for k, v in b.items():
            if k in a and isinstance(a[k], dict):
                merge(a[k], v)
            elif v:
                a[k] = deepcopy(v)
        return a

    segments = []
    for k, v in flat.items():
        parts = k.split('_')[:-drop_last]
        seg = {parts[-1:][0]: v}
        for part in reversed(parts[:-1]):
            seg = {part: seg}
        segments.append(seg)

    return reduce(merge, segments)
    

async def monitor_loop():
    global redis, db, metrics
    while True:
        log.debug("updating metrics")
        metrics.update(await database_feeds(db))
        metrics.update(await database_entries(db))
        tree = tree_split(metrics, drop_last=1)
        #await redis.mset('metrics:timestamp', time(), *{'metrics:' + k:v for k,v in metrics.items() if v})
        await publish(redis, 'ui', {'event': 'metrics_feeds', 'data': tree['database']['feeds']})
        await publish(redis, 'ui', {'event': 'metrics_entries', 'data': tree['database']['entries']})
        await sleep(METRICS_INTERVAL)
    redis.close()
    await redis.wait_closed()


@app.listener('after_server_start')
async def init_connections(sanic, loop):
    """Bind the database and Redis client to Sanic's event loop."""

    global redis, db
    redis = await connect_redis()
    motor = AsyncIOMotorClient(MONGO_SERVER, io_loop=loop)
    db = motor[DATABASE_NAME]
    log.debug("adding task")
    app.add_task(loop.create_task(monitor_loop()))


if __name__ == '__main__':
    log.debug("Beginning run.")
    app.run(host=BIND_ADDRESS, port=HTTP_PORT, debug=DEBUG)
