CHECK_INTERVAL?=5
FETCH_INTERVAL?=15
MONGO_SERVER?=localhost:27017
DATABASE_NAME?=feeds
ITEM_SOCKET?=tcp://127.0.0.1:4675

fetch:
	python fetcher.py

deps:
	pip install --retries 10 -U -r requirements.txt
