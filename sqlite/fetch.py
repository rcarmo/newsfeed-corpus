from time import time
from asyncio import get_event_loop, Semaphore, gather, ensure_future
from aiohttp import ClientSession
from xml.etree import ElementTree
from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.kv import JSONKeyStore

async def fetch_one(session, feed, db):
    url = feed.value.get("url")
    print("Fetching {0}".format(url))
    try:
        async with session.get(url) as response:
            text = await response.text()
            feed.value.update({"text": text, "last_status": response.status, "last_fetched": time()})
            feed.save()
            return feed, response.status
    except Exception as e:
        print(e)
        feed.value.update({"last_status": 0, "last_fetched": time()})
        feed.save()
        return feed, 0
        pass

async def throttle(sem, session, feed, db):
    async with sem:
        res = await fetch_one(session, feed, db)
        print(res[0].value["url"],res[1])

async def fetcher(db):
    sem = Semaphore(100)
    tasks = []
    async with ClientSession() as session:
        for feed in db.model.select().where(db.model.key.startswith("feed:")):
            task = ensure_future(throttle(sem, session, feed, db))
            tasks.append(task)

        responses = gather(*tasks)
        await responses

def feeds_from_opml(filename):
    tree = ElementTree.parse(filename)
    for feed in tree.findall('.//outline'):
        if feed.get('xmlUrl'):
            yield {'title': feed.get('title'),
                   'url': feed.get('xmlUrl')}

def update_database(db, filename):
    for feed in feeds_from_opml(filename):
        if not "feed:" + feed['url'] in db:
            feed['last_fetched'] = 0
            db["feed:" + feed['url']] = feed

if __name__ == '__main__':
    db = JSONKeyStore(database=SqliteExtDatabase('/tmp/feeds.db'))
    update_database(db,'feeds.opml')
    loop = get_event_loop()
    tasks = ensure_future(fetcher(db))
    loop.run_until_complete(tasks)
