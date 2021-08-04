#!/usr/bin/env python3

import logging
import os
from io import BytesIO

import pandas as pd
import requests
import sqlalchemy


TNS_API_KEY = os.environ['TNS_API_KEY']
TNS_BOT_ID = os.environ['TNS_BOT_ID']
TNS_BOT_NAME = os.environ['TNS_BOT_NAME']


ENGINE = sqlalchemy.create_engine(sqlalchemy.engine.url.URL(
    drivername='postgresql+psycopg2',
    username='catalog',
    password='catalog',
    database='catalog',
))


CHUNKSIZE = 1 << 10


CATALOG_URL = 'https://www.wis-tns.org/system/files/tns_public_objects/tns_public_objects.csv.zip'


def download_table():
    with requests.post(
        CATALOG_URL,
        headers={
            'user-agent': 'tns_marker{{"tns_id":"{id}","type": "bot", "name":"{name}"}}'.format(
                id=TNS_BOT_ID,
                name=TNS_BOT_NAME,
            )
        },
        data={
            'api_key': (None, TNS_API_KEY)
        },
    ) as response:
        return response.content


def upload_table(data):
    df = pd.read_csv(
        BytesIO(data),
        skiprows=1,
        compression='zip',
    )
    df.to_sql('tns', ENGINE, chunksize=CHUNKSIZE, index=False)


def main():
    logging.basicConfig(level=logging.INFO)

    logging.info('Downloading table')
    data = download_table()
    logging.info('Upload table to DBMS')
    upload_table(data)


if __name__ == '__main__':
    main()
