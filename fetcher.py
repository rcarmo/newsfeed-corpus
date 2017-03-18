#!/usr/bin/env python3

""" Feed fetcher """

from datetime import datetime, timedelta
from hashlib import sha1
from asyncio import get_event_loop, Semaphore, gather, ensure_future, set_event_loop_policy, sleep
from aiozmq.rpc import connect_pipeline, AttrHandler, serve_pipeline, method
from uvloop import EventLoopPolicy
from aiohttp import ClientSession
from motor.motor_asyncio import AsyncIOMotorClient
from config import log, CHECK_INTERVAL, FETCH_INTERVAL, MONGO_SERVER, DATABASE_NAME, ENTRY_PARSER,  FEED_FETCHER, get_profile

class Handler(AttrHandler):
    """0MQ handler"""

    @method
    async def profile(self):
        return get_profile()


async def server():
    """Server pipeline"""

    log.info("RPC Server starting")
    listener = await serve_pipeline(Handler(), bind=FEED_FETCHER)
    await listener.wait_closed()


async def fetch_one(session, feed, client, database):
    """Fetch a single feed"""

    url = feed['url']
    checksum = feed.get('checksum', None)
    notify = False
    headers = {}

    log.debug("Fetching %s", url)

    if 'etag' in feed:
        headers['etag'] = feed['etag']
    if 'last_modified' in feed:
        headers['if-modified-since'] = feed['last_modified']

    try:
        async with session.get(url, headers=headers) as response:
            text = await response.text()
            update = {
                'last_status': response.status, # TODO: check behavior for 301/302
                'last_fetched': datetime.now(),
            }
            if response.status == 200:
                if 'checksum' not in feed or feed['checksum'] != checksum:
                    notify = True
                update['raw'] = text
                update['checksum'] = sha1(text.encode('utf-8')).hexdigest()

            if 'etag' in response.headers:
                update['etag'] = response.headers['etag']

            if 'last-modified' in response.headers:
                update['last_modified'] = response.headers['last-modified']

            await database.feeds.update_one({'url': url}, {'$set': update})

            if notify:
                log.debug("Notifying...")
                await client.notify.parse(url, text)

            return feed, response.status

    except Exception as e:
        log.error(e)
        await database.feeds.update_one({'url': url},
                                        {'$set': {'last_status': 0,
                                                  'last_fetched': datetime.now()}})
        return feed, 0


async def throttle(sem, session, feed, client, database):
    """Throttle number of simultaneous requests"""

    async with sem:
        res = await fetch_one(session, feed, client, database)
        log.info("%s: %d", res[0]['url'], res[1])


async def fetcher(database):
    """Fetch all the feeds"""

    sem = Semaphore(100)

    while True:
        client = await connect_pipeline(connect=ENTRY_PARSER)
        tasks = []
        threshold = datetime.now() - timedelta(seconds=FETCH_INTERVAL)

        async with ClientSession() as session:
            log.info("Beginning run.")
            async for feed in database.feeds.find({}):
                log.debug("Checking %s", feed['url'])
                last_fetched = feed.get('last_fetched', threshold)
                if last_fetched <= threshold:
                    task = ensure_future(throttle(sem, session, feed, client, database))
                    tasks.append(task)

            responses = gather(*tasks)
            await responses
            log.info("Run complete, sleeping %ds...", CHECK_INTERVAL)
            await sleep(CHECK_INTERVAL)


def main():
    """Main function"""
    set_event_loop_policy(EventLoopPolicy())
    conn = AsyncIOMotorClient(MONGO_SERVER)
    database = conn[DATABASE_NAME]

    loop = get_event_loop()
    ensure_future(server())
    ensure_future(fetcher(database))
    try:
        loop.run_forever()
    finally:
        loop.close()


if __name__ == '__main__':
    main()
