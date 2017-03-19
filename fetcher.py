#!/usr/bin/env python3

""" Feed fetcher """

from datetime import datetime, timedelta
from hashlib import sha1
from asyncio import get_event_loop, Semaphore, gather, ensure_future, set_event_loop_policy, sleep
from aiozmq.rpc import connect_pipeline, AttrHandler, serve_pipeline, method
from traceback import format_exc
from uvloop import EventLoopPolicy
from aiohttp import ClientSession, TCPConnector
from aioredis import create_redis
from motor.motor_asyncio import AsyncIOMotorClient
from config import log, CHECK_INTERVAL, FETCH_INTERVAL, MONGO_SERVER, DATABASE_NAME, MAX_CONCURRENT_REQUESTS
from common import connect_queue, dequeue, enqueue
from bson.objectid import ObjectId   

async def fetch_one(session, feed, client, database, queue):
    """Fetch a single feed"""

    url = feed['url']
    checksum = feed.get('checksum', None)
    changed = False
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
                    changed = True
                update['raw'] = text
                update['checksum'] = sha1(text.encode('utf-8')).hexdigest()

            if 'etag' in response.headers:
                update['etag'] = response.headers['etag']

            if 'last-modified' in response.headers:
                update['last_modified'] = response.headers['last-modified']

            await database.feeds.update_one({'url': url}, {'$set': update})

            if changed:
                log.debug("Notifying...")  
                await enqueue(queue, 'parser', {
                    "_id": feed['_id'],
                    "scheduled_at": datetime.now()
                })
            return feed, response.status

    except Exception as e:
        log.error(format_exc())
        await database.feeds.update_one({'url': url},
                                        {'$set': {'last_status': 0,
                                                  'last_fetched': datetime.now()}})
        return feed, 0


async def throttle(sem, session, feed, client, database, queue):
    """Throttle number of simultaneous requests"""

    async with sem:
        res = await fetch_one(session, feed, client, database, queue)
        log.info("%s: %d", res[0]['url'], res[1])


async def fetcher(database):
    """Fetch all the feeds"""

    # disable certificate validation to cope with self-signed certificates in some feed back-ends
    client = ClientSession(connector=TCPConnector(verify_ssl=False))
    sem = Semaphore(MAX_CONCURRENT_REQUESTS)

    queue = await connect_queue()
    while True:
        log.info("Beginning run.")
        tasks = []
        threshold = datetime.now() - timedelta(seconds=FETCH_INTERVAL)
        async with ClientSession() as session:
            while True:
                try:
                    job = await dequeue(queue, 'fetcher')
                    feed = await database.feeds.find_one({'_id': job['_id']})
                    last_fetched = feed.get('last_fetched', threshold)
                    if last_fetched <= threshold:
                        task = ensure_future(throttle(sem, session, feed, client, database, queue))
                        tasks.append(task)
                except Exception as e:
                    log.error(e)
                    break
            responses = gather(*tasks)
            await responses
            log.info("Run complete, sleeping %ds...", CHECK_INTERVAL)
            await sleep(CHECK_INTERVAL)
    queue.close()
    await queue.wait_closed()


def main():
    """Setup coroutines and kickstart fetcher"""
    set_event_loop_policy(EventLoopPolicy())

    motor = AsyncIOMotorClient(MONGO_SERVER)
    database = motor[DATABASE_NAME]

    loop = get_event_loop()
    ensure_future(fetcher(database))
    try:
        loop.run_forever()
    finally:
        loop.close()


if __name__ == '__main__':
    main()
