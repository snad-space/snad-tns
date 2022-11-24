#!/usr/bin/env python3

import logging
import os
import sys
from io import BytesIO

import pandas as pd
import requests
import sqlalchemy


TNS_API_KEY = os.environ['TNS_API_KEY']
TNS_BOT_ID = os.environ['TNS_BOT_ID']
TNS_BOT_NAME = os.environ['TNS_BOT_NAME']


if len(sys.argv) <= 1:
    HOSTNAME = None
elif len(sys.argv) == 2:
    HOSTNAME = sys.argv[1]
else:
    raise RuntimeError('Too many command-line arguments')



ENGINE = sqlalchemy.create_engine(sqlalchemy.engine.url.URL(
    host = HOSTNAME,
    drivername='postgresql+psycopg2',
    username='catalog',
    password='catalog',
    database='catalog',
))


TABLE_NAME = 'tns'


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


def drop_and_replace(df, table):
    with ENGINE.connect() as connection, connection.begin():
        connection.execute('DROP TABLE IF EXISTS {table}'.format(table=table))
        df.to_sql(table, con=connection, chunksize=CHUNKSIZE, index=False)
        connection.execute('ALTER TABLE {table} ADD PRIMARY KEY ("objid")'.format(table=table))
        connection.execute('CREATE INDEX {table}_name_idx ON {table} ("name")'.format(table=table))
        connection.execute('ALTER TABLE {table} ADD COLUMN coord spoint'.format(table=table))
        connection.execute('UPDATE {table} SET coord = spoint("ra" * pi() / 180.0, "declination" * pi() / 180.0)'.format(table=table))
        connection.execute('ALTER TABLE {table} ALTER COLUMN coord SET NOT NULL'.format(table=table))
        connection.execute('CREATE INDEX {table}_coord_idx ON {table} USING GIST (coord)'.format(table=table))


def upload_table(data):
    df = pd.read_csv(
        BytesIO(data),
        skiprows=1,
        compression='zip',
    )
    drop_and_replace(df, TABLE_NAME)


def main():
    logging.basicConfig(level=logging.INFO)

    logging.info('Downloading table')
    data = download_table()
    logging.info('Upload table to DBMS')
    upload_table(data)


if __name__ == '__main__':
    main()
