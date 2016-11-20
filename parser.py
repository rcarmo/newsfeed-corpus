""" Feed parser """

from datetime import datetime
from hashlib import sha1
from asyncio import get_event_loop, set_event_loop_policy
from motor.motor_asyncio import AsyncIOMotorClient
from aiozmq.rpc import AttrHandler, serve_pipeline, method
from uvloop import EventLoopPolicy
from config import ITEM_SOCKET, log, DATABASE_NAME, MONGO_SERVER
from feedparser import parse as feed_parse


def get_entry_content(entry):
    """Select the best content from an entry"""

    candidates = entry.get('content', [])
    if 'summary_detail' in entry:
        candidates.append(entry.summary_detail)
    for candidate in candidates:
        if hasattr(candidate, 'type'): # speedparser doesn't set this
            if 'html' in candidate.type:
                return candidate.value
    if candidates:
        try:
            return candidates[0].value
        except AttributeError: # speedparser does this differently
            return candidates[0]['value']
    return ''


def get_entry_date(entry):
    """Select the best timestamp for an entry"""
    for header in ['modified', 'issued', 'created']:
        when = entry.get(header+'_parsed', None)
        if when:
            return when
    return datetime.now()


def get_entry_id(entry):
    """Get a useful id from a feed entry"""

    if 'id' in entry and entry.id:
        if isinstance(entry.id, dict):
            return entry.id.values()[0]
        return entry.id

    content = get_entry_content(entry)
    if content:
        return sha1(content.encode('utf-8')).hexdigest()
    if 'link' in entry:
        return entry.link
    if 'title' in entry:
        return sha1(entry.title.encode('utf-8')).hexdigest()


class Handler(AttrHandler):

    def __init__(self, db):
        self.database = db

    @method
    async def parse(self, url, text):
        log.info("Parsing %s", url)
        result = feed_parse(text)
        if not len(result.entries):
            log.info('No valid entries')
            return
        async for entry in result.entries:
            log.info(entry.link)
            uuid = get_entry_id(entry)
            when = get_entry_date(entry)
            body = get_entry_content(entry)

            await self.database.entries.update_one({'_id': uuid},
                                                   {'$set': {"date": when, "body": body, "url": entry.link}}, upsert=True)

async def server(database):
    log.info("Server starting")
    listener = await serve_pipeline(Handler(database), bind=ITEM_SOCKET)
    await listener.wait_closed()

def main():
    set_event_loop_policy(EventLoopPolicy())
    conn = AsyncIOMotorClient(MONGO_SERVER)
    database = conn[DATABASE_NAME]
    loop = get_event_loop()
    loop.run_until_complete(server(database))

if __name__ == '__main__':
    main()
