#!/usr/bin/env python3

""" Feed parser """

from time import mktime
from datetime import datetime
from hashlib import sha1
from asyncio import get_event_loop, set_event_loop_policy
from traceback import format_exc
from motor.motor_asyncio import AsyncIOMotorClient
from uvloop import EventLoopPolicy
from feedparser import parse as feed_parse
from bs4 import BeautifulSoup
from langdetect import detect
from common import connect_queue, dequeue, enqueue, safe_id
from config import DATABASE_NAME, MONGO_SERVER, get_profile, log
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from nltk.stem import RSLPStemmer
from gensim import corpora, models
from langkit import extract_keywords

STOP_WORDS = {'en': stopwords.words('english'), 
              'pt': stopwords.words('portuguese')}

STEMMERS = {'en': PorterStemmer(),
            'pt': RSLPStemmer()}

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
            return datetime.fromtimestamp(mktime(when))
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


def get_plaintext(html):
    """Scrub out tags and extract plaintext"""

    soup = BeautifulSoup(html)
    for script in soup(["script", "style"]):
        script.extract()
    return soup.get_text()


def tokenize(plaintext, language):
    # TODO: move this to langkit
    try:
        stop_words = STOP_WORDS[language]
        stemmer = STEMMERS[language]
    except KeyError:
        log.error(format_exc())
        return
    # Tokenize, remove stop words and stem
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = [stemmer.stem(i) for i in tokenizer.tokenize(plaintext.lower()) if not i in stop_words]
    return tokens


def lda(tokens):
    # Perform Latent Dirchelet Allocation
    dictionary = corpora.Dictionary(tokens)
    corpus = [dictionary.doc2bow(token) for token in tokens]
    lda_model = gensim.models.ldamodel.LdaModel(corpus, num_topics=3, id2word=dictionary, passes=20)
    return lda_model


async def parse(database, feed):
    """Parse a feed into its constituent entries"""

    result = feed_parse(feed['raw'])
    if not len(result.entries):
        log.info('%s: No valid entries', feed['_id'])
        return
    else:
        log.info('%s: %d entries', feed['_id'], len(result.entries))
        # TODO: turn this into a bulk insert
        for entry in result.entries:
            log.debug(entry.link)
            when = get_entry_date(entry)
            body = get_entry_content(entry)
            plaintext = entry.title + " " + get_plaintext(body)
            lang = detect(plaintext)
            await database.entries.update_one({'_id': safe_id(entry.link)},
                                              {'$set': {"date": when,
                                                        "title": entry.title,
                                                        "body": body,
                                                        "plaintext": plaintext,
                                                        "lang": lang,
                                                        "keywords": extract_keywords(plaintext, lang),
                                                        "tokens": tokenize(plaintext, lang),
                                                        "url": entry.link}},
                                              upsert=True)


async def item_handler(database):
    """Break down feeds into individual items"""

    queue = await connect_queue()
    log.info("Beginning run.")
    while True:
        try:
            job = await(dequeue(queue, 'parser'))
            feed = await database.feeds.find_one({'_id': job['_id']})
            await parse(database, feed)
        except Exception:
            log.error(format_exc())
            break
    queue.close()
    await queue.wait_closed()


def main():
    """Main loop"""

    set_event_loop_policy(EventLoopPolicy())
    conn = AsyncIOMotorClient(MONGO_SERVER)
    database = conn[DATABASE_NAME]
    loop = get_event_loop()
    try:
        loop.run_until_complete(item_handler(database))
    finally:
        loop.close()

if __name__ == '__main__':
    main()
