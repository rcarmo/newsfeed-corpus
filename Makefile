CHECK_INTERVAL?=5
FETCH_INTERVAL?=15
MONGO_SERVER?=localhost:27017
DATABASE_NAME?=feeds
FEED_FETCHER?=tcp://127.0.0.1:4674
ENTRY_PARSER?=tcp://127.0.0.1:4675
PORT?=8000

fetch:
	python fetcher.py

deps:
	pip install --retries 10 -U -r requirements.txt
