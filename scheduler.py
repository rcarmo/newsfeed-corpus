#!/usr/bin/env python3

""" Feed enumerator """

from asyncio import ensure_future, get_event_loop, set_event_loop_policy, sleep
from config import (CHECK_INTERVAL, DATABASE_NAME, FETCH_INTERVAL,
                    MONGO_SERVER, log)
from datetime import datetime, timedelta

from common import REDIS_NAMESPACE, connect_redis, enqueue
from motor.motor_asyncio import AsyncIOMotorClient
from uvloop import EventLoopPolicy


async def scan_feeds(db):
    """Enumerate all feeds and queue them for fetching"""

    # let importer run first while we're testing
    await sleep(5)

    log.info("Beginning run.")

    while True:
        threshold = datetime.now() - timedelta(seconds=FETCH_INTERVAL)
        log.debug(threshold)
        queue = await connect_redis()
        log.info("Scanning feed list.")
        log.debug("Starting loop")
        count = 0
        async for feed in db.feeds.find({'last_fetched': {'$lt': threshold}}):
            count = count + 1
            url = feed['url']
            log.debug("Checking %d: %s", count, url)
            log.debug("Queueing %s", url)
            await enqueue(queue, "fetcher", {
                "_id": feed['_id'],
                "scheduled_at": datetime.now()
            })
            if not (count % 10):
               await queue.hset(REDIS_NAMESPACE + 'status', 'feed_count', count)
        await queue.hset(REDIS_NAMESPACE + 'status', 'feed_count', count)
        queue.close()
        await queue.wait_closed()
        log.info("Run complete, sleeping %ds...", CHECK_INTERVAL)
        await sleep(CHECK_INTERVAL)


def main():
    """Setup event loop and start coroutines"""

    set_event_loop_policy(EventLoopPolicy())
    loop = get_event_loop()

    client = AsyncIOMotorClient(MONGO_SERVER)
    database = client[DATABASE_NAME]

    ensure_future(scan_feeds(database))
    try:
        loop.run_forever()
    finally:
        loop.close()


if __name__ == '__main__':
    main()
