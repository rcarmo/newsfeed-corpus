#!/usr/bin/env python3

"""OPML importer"""

from asyncio import (Semaphore, ensure_future, gather, get_event_loop,
                     set_event_loop_policy)
from config import (DATABASE_NAME, DATE_FORMAT, FETCH_INTERVAL, MONGO_SERVER,
                    log)
from datetime import datetime
from time import sleep, strftime, time
from xml.etree import ElementTree

from aiohttp import ClientSession
from common import REDIS_NAMESPACE, connect_redis, safe_id
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from uvloop import EventLoopPolicy


def feeds_from_opml(filename):
    """Extract useful attributes from OPML"""

    tree = ElementTree.parse(filename)
    for feed in tree.findall('.//outline'):
        if feed.get('xmlUrl'):
            yield {'title': feed.get('title'),
                   'url': feed.get('xmlUrl')}


async def update_database(db, filename):
    """Create indexes and import feeds"""

    entries = db.entries
    await db.entries.create_index([("date", DESCENDING)])
    await db.entries.create_index([("url", ASCENDING)])
    feeds = db.feeds
    await db.feeds.create_index([("url", ASCENDING)])
    # TODO: turn this into a bulk upsert
    for feed in feeds_from_opml(filename):
        if not await feeds.find_one({'url': feed['url']}):
            log.debug("Inserting %s" % feed)
            feed['_id'] = safe_id(feed['url'])
            feed['created'] = datetime.now()
            try:
                await feeds.insert_one(feed)
            except DuplicateKeyError as e:
                log.debug(e)
    redis = await connect_redis()
    await redis.hset(REDIS_NAMESPACE + 'status', 'feed_count', await db.feeds.count_documents({}))


if __name__ == '__main__':

    set_event_loop_policy(EventLoopPolicy())
    loop = get_event_loop()

    c = AsyncIOMotorClient(MONGO_SERVER)
    db = c[DATABASE_NAME]
    try:
        loop.run_until_complete(update_database(db,'feeds.opml'))
    finally:
        loop.close()
