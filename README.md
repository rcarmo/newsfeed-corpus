# newsfeed-corpus

## What

An ongoing attempt at tying together various ML techniques for trending topic and sentiment analysis.

## Why

I needed a readily available corpus for doing text analytics and sentiment analysis, so I decided to make one from my RSS feeds.

## How

This is the "dumb" part of the pipeline -- the corpus is fed into [Azure ML][aml] and the [Cognitive Services APIs][csa] for the nice stuff, so this is mostly about fetching, parsing and doing basic analysis on feeds.

## Architecture

This is a set of independent worker processes written in Python 3.5:

* [x] `import.py` is a one-shot OPML importer
* [x] `fetcher.py` fetches feeds and stores them on DocumentDB/MongoDB
* [x] `parser.py` parses updated feeds into separate items and performs language detection
* [ ] `api.py` provides a REST API to retrieve recent items
* [ ] `topics.py` does topic detection

Processes are written to leverage `asyncio`  and talk via [0MQ][0mq], so they can be deployed on separate machines. [piku][piku] is currently used for deployment, but packaging and deploying them using Docker and [alpine-python][ap] is trivial.

[0mq]: https://github.com/aio-libs/aiozmq
[csa]: https://www.microsoft.com/cognitive-services
[aml]: https://studio.azureml.net
[ap]: github.com/rcarmo/alpine-python/
[piku]: https://github.com/rcarmo/piku
