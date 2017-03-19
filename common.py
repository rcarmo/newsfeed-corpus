""" Common functions """
from hashlib import sha1
from uuid import uuid4
from time import time
from json import dumps, loads
from urllib.parse import urlparse
from asyncio import get_event_loop
from aioredis import create_redis
from bson import json_util
from config import REDIS_SERVER


def safe_id(url):
    """Build a DocumentDB-safe and URL-safe ID that is still palatable to humans"""
    fragments = urlparse(url)
    safe = fragments.netloc + fragments.path.replace('/', '_').replace('+', '-')
    if fragments.params or fragments.query:
        # Add a short hash to distinguish between feeds from same site
        safe += sha1(bytes(url, 'utf-8')).hexdigest()[6]
    safe.rstrip('_-')
    return safe

class AsyncIOQueue():
    """Simple wrapper for IPC"""

    async def __init__(self, server=REDIS_SERVER):
        self.server = await create_redis(server.split(':'), loop=get_event_loop())

    async def register_worker(self, kind):
        """Register a worker in redis, with an optional type"""
        worker_id = str(uuid4())
        await self.server.hset("workers", worker_id, kind)
        return worker_id

    async def enqueue(self, queue_name, data):
        """Enqueue an object in a given redis queue"""
        return await self.server.lpush(queue_name, dumps(data, default=json_util.default))

    async def dequeue(self, queue_name):
        """Blocking dequeue from Redis"""
        data = await self.server.brpop(queue_name)
        return loads(data, object_hook=json_util.object_hook)
