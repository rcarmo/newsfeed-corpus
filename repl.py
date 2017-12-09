#!/usr/bin/env python3

""" REPL for database inspection """

from config import (CHECK_INTERVAL, DATABASE_NAME, FETCH_INTERVAL,
                    MAX_CONCURRENT_REQUESTS, MONGO_SERVER, log)
from datetime import datetime, timedelta
from pymongo import MongoClient
from code import interact
from bpython import embed

def main():
    client = MongoClient(MONGO_SERVER)
    db = client[DATABASE_NAME]

    embed(locals_=locals())

if __name__ == '__main__':
    main()
