# newsfeed-corpus

<img src="https://raw.githubusercontent.com/rcarmo/newsfeed-corpus/master/screenshots/2017-12-10.png" style="max-width: 100%; height: auto">

## What

An ongoing attempt at tying together various ML techniques for trending topic and sentiment analysis, coupled with some experimental Python `async` coding, a distributed architecture, EventSource and lots of Docker goodness.

## Why

I needed a readily available corpus for doing text analytics and sentiment analysis, so I decided to make one from my RSS feeds.

Things escalated quickly from there on several fronts:

* I decided I wanted this to be fully distributed, so I split the logic into several worker processes who coordinate via [Redis][redis] queues, orchestrated (and deployed) using `docker-compose`
* I decided to take a ride on the bleeding edge and refactored everything to use `asyncio/uvloop` (as well as [Sanic][sanic] for the web front-end)
* Rather than just consuming cognitive APIs, I also decided to implement a few NLP processing techniques (I started with a RAKE keyword extractor, and am now looking at NLTK-based tagging)
* Instead of using React, I went with RiotJS, largely because I wanted to be able to deploy new visual components without a build step.
* I also started using this as a "complex" Docker/Kubernetes demo, which meant some flashy features (like a graphical dashboard) started taking precedence.

## How

This was originally the "dumb" part of the pipeline -- the corpus was fed into [Azure ML][aml] and the [Cognitive Services APIs][csa] for the nice stuff, so this started out mostly focusing fetching, parsing and filing away feeds.

It's now a rather more complex beast than I originally bargained for. Besides acting as a technology demonstrator for a number of things (including odds and ends like how to bundle NLTK datasets inside Docker) it is currently pushing the envelope on [my Python Docker containers][ap], which now feature Python 3.6.3 atop Ubuntu LTS.

## ToDo

* [ ] move to [billboard.js](https://github.com/naver/billboard.js)
* [ ] Add `auth0` support

### Architecture

* [x] `import.py` is a one-shot OPML importer (you should place your own `feeds.opml` in the root directory)
* [ ] `metrics.py` keeps tabs on various stats and pushes them out every few seconds
* [x] `scheduler.py` iterates through the database and queues feeds for fetching 
* [x] `fetcher.py` fetches feeds and stores them on DocumentDB/MongoDB
* [x] `parser.py` parses updated feeds into separate items and performs:
      [x] language detection
      [x] keyword extraction (using `langkit.py`)
      [ ] basic sentiment analysis
* [ ] `cortana.py` (WIP) will do topic detection and sentiment analysis
* [ ] `web.py` (WIP) provides a simple web front-end and REST API to navigate the results

Processes are written to leverage `asyncio/uvloop` and interact via [Redis][redis] (previously they interacted via [ZeroMQ][0mq], but I'm already playing around with deploying this on [Swarm and an Azure VM scaleset][swarm]). 

A Docker compose file is supplied for running the entire stack locally - you can tweak it up to version `3` and get things running on Swarm if you manually push the images to a private registry first, but I'll automate that once things are a little more stable.

[0mq]: https://github.com/aio-libs/aiozmq
[csa]: https://www.microsoft.com/cognitive-services
[aml]: https://studio.azureml.net
[ap]: https://github.com/rcarmo/alpine-python
[swarm]: https://github.com/rcarmo/azure-docker-swarm-cluster
[sanic]: http://sanic.readthedocs.io
[piku]: https://github.com/rcarmo/piku
[redis]: http://redis.io
