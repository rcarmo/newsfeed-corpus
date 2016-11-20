#!/usr/bin/env python3

"""OPML importer"""

from time import time, sleep, strftime
from asyncio import get_event_loop, Semaphore, gather, ensure_future
from aiohttp import ClientSession
from xml.etree import ElementTree

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from config import log, FETCH_INTERVAL, MONGO_SERVER, DATABASE_NAME, DATE_FORMAT


def feeds_from_opml(filename):
    """Extract useful attributes from OPML"""

    tree = ElementTree.parse(filename)
    for feed in tree.findall('.//outline'):
        if feed.get('xmlUrl'):
            yield {'title': feed.get('title'),
                   'url': feed.get('xmlUrl')}


def update_database(db, filename):
    """Create indexes and import feeds"""

    entries = db.entries
    db.entries.create_index([("date", DESCENDING)])
    db.entries.create_index([("url", ASCENDING)])
    feeds = db.feeds
    db.feeds.create_index([("url", ASCENDING)])
    # TODO: turn this into a bulk upsert
    for feed in feeds_from_opml(filename):
        if not feeds.find_one({'url': feed['url']}):
            log.debug("Inserting %s" % feed)
            feed['_id'] = feed['url']
            feed['created'] = datetime.now()
            feeds.insert_one(feed)


if __name__ == '__main__':
    c = MongoClient(MONGO_SERVER)
    db = c[DATABASE_NAME]
    update_database(db,'feeds.opml')
