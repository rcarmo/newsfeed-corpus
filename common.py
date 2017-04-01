#!/bin/env python3

""" Common functions """

from hashlib import sha1
from uuid import uuid4
from time import time
from json import dumps, loads
from urllib.parse import urlparse
from asyncio import get_event_loop
from aioredis import create_redis
from bson import json_util
from config import log, REDIS_SERVER, REDIS_NAMESPACE

def safe_id(url):
    """Build a DocumentDB-safe and URL-safe ID that is still palatable to humans"""
    fragments = urlparse(url)
    safe = fragments.netloc + fragments.path.replace('/', '_').replace('+', '-')
    if fragments.params or fragments.query:
        # Add a short hash to distinguish between feeds from same site
        safe += sha1(bytes(url, 'utf-8')).hexdigest()[6]
    return safe.rstrip('_-')

async def connect_redis(loop=None):
    """Connect to a Redis server"""
    if not loop:
        loop = get_event_loop()
    return await create_redis(REDIS_SERVER.split(':'), loop=loop)

async def enqueue(server, queue_name, data):
    """Enqueue an object in a given redis queue"""
    return await server.rpush(REDIS_NAMESPACE + queue_name, dumps(data, default=json_util.default))

async def dequeue(server, queue_name):
    """Blocking dequeue from Redis"""
    _, data = await server.blpop(REDIS_NAMESPACE + queue_name, 0)
    return loads(data, object_hook=json_util.object_hook)