#!/usr/bin/env python3

""" Feed enumerator """

from datetime import datetime, timedelta
from asyncio import get_event_loop, ensure_future, set_event_loop_policy, sleep
from uvloop import EventLoopPolicy
from motor.motor_asyncio import AsyncIOMotorClient
from config import CHECK_INTERVAL, DATABASE_NAME, FETCH_INTERVAL, MONGO_SERVER, log
from common import connect_redis, enqueue, REDIS_NAMESPACE

async def scan_feeds(db):
    """Enumerate all feeds and queue them for fetching"""

    # let importer run first while we're testing
    await sleep(5)

    log.info("Beginning run.")

    while True:
        threshold = datetime.now() - timedelta(seconds=FETCH_INTERVAL)
        queue = await connect_redis()
        log.info("Scanning feed list.")
        await queue.hset(REDIS_NAMESPACE + 'status', 'feed_count', await db.feeds.count())
        async for feed in db.feeds.find({}):
            url = feed['url']
            #log.debug("Checking %s", url)
            last_fetched = feed.get('last_fetched', threshold)
            if last_fetched <= threshold:
                log.debug("Queueing %s", url)
                await enqueue(queue, "fetcher", {
                    "_id": feed['_id'],
                    "scheduled_at": datetime.now()
                })
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
