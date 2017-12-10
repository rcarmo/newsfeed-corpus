#!/bin/env python3

""" Web server """

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


@app.route('/events')
async def sse(request):
    async def streaming_fn(response):
        i = 1
        [ch] = await subscribe(redis, 'ui')
        while (await ch.wait_message()):
            msg = await ch.get_json()
            s = ''
            if 'event' in msg:
                s = s + 'event: ' + msg['event'] + '\r\n' 
            s = s + 'data: ' + dumps(msg) + '\r\n\r\n'
            response.write(s.encode())
            i += 1
    return stream(streaming_fn, content_type='text/event-stream')


@app.route('/status', methods=['GET'])
async def get_status(req):
    """Status endpoint for the web UI - will expose all counters."""

    return json({
        "feed_count": await redis.hget(REDIS_NAMESPACE + 'status', 'feed_count'),
        "item_count": await redis.hget(REDIS_NAMESPACE + 'status', 'item_count')
    })


@app.route('/stats/fetcher', methods=['GET'])
async def handler(req):
    cursor = db.feeds.aggregate([{"$group": {"_id": "$last_status", "count": {"$sum": 1}}}, 
                                 {"$sort":{"count":-1}} ])
    return json({'total': await db.feeds.count(),
                 'status': {i['_id']: i['count'] async for i in cursor}})


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
    
    return json({'total': await db.entries.count(),
                 'status': 


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


# Add a route-specific timeout for the SSE handler
class CustomHttpProtocol(HttpProtocol):
    def on_message_complete(self):
        if self.url == b'/events':
            self.request_timeout = 1000
        super().on_message_complete()


# Map static assets
app.static('/', './static')


@app.listener('after_server_start')
async def init_connections(sanic, loop):
    """Bind the database and Redis client to Sanic's event loop."""

    global redis, db
    redis = await connect_redis()
    motor = AsyncIOMotorClient(MONGO_SERVER, io_loop=loop)
    db = motor[DATABASE_NAME]


if __name__ == '__main__':
    log.debug("Beginning run.")
    app.run(host=BIND_ADDRESS, port=HTTP_PORT, workers=cpu_count(), debug=DEBUG, protocol=CustomHttpProtocol)
