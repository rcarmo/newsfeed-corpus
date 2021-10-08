#!/bin/env python3

""" Common functions """

from asyncio import get_event_loop, sleep
from config import REDIS_NAMESPACE, REDIS_SERVER, log
from hashlib import sha1
from json import dumps, loads
from time import time
from urllib.parse import urlparse
from uuid import uuid4

from aioredis import from_url
from bson import json_util


def retry(attempts, on_exception, interval=0):
    def wrap(func):
        def f_retry(*args, **kwargs):
            for i in range(attempts):
                try: 
                    return func(*args, **kwargs)
                except on_exception as e:
                    log.debug("retry %d for %s(%s, %s), waiting %d" % (i, func,args,kwargs, interval))
                    sleep(interval)
                    continue
        return f_retry
    return wrap


def safe_id(url):
    """Build a CosmosDB-safe and URL-safe ID that is still palatable to humans"""
    fragments = urlparse(url)
    safe = fragments.netloc + fragments.path.replace('/', '_').replace('+', '-')
    if fragments.params or fragments.query:
        # Add a short hash to distinguish between feeds from same site
        safe += sha1(bytes(url, 'utf-8')).hexdigest()[6]
    return safe.rstrip('_-')


async def connect_redis(loop=None):
    """Connect to a Redis server"""

    return await from_url(REDIS_SERVER)

async def enqueue(conn, queue_name, data):
    """Enqueue an object in a given redis queue"""
    return await conn.rpush(REDIS_NAMESPACE + queue_name, dumps(data, default=json_util.default))

async def dequeue(conn, queue_name):
    """Blocking dequeue from Redis"""
    _, data = await conn.blpop(REDIS_NAMESPACE + queue_name, 0)
    return loads(data, object_hook=json_util.object_hook)

async def publish(conn, topic_name, data):
    """Publish data"""
    _ = await conn.publish_json(topic_name, data)

async def subscribe(conn, topic_name):
    """Subscribe to topic data"""
    chan = conn.pubsub()
    await chan.subscribe(topic_name)
    return chan

async def unsubscribe(conn, topic_name):
    """Unsubscribe from topic data"""
    pubsub = conn.pubsub()
    _ = await pubsub.unsubscribe(topic_name)
