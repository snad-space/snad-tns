#!/usr/bin/env python3

import logging
from time import sleep

import psycopg2


def main():
    while True:
        try:
            with psycopg2.connect(host='tns-catalog-sql', user='app', dbname='catalog') as con:
                with con.cursor() as cur:
                    cur.execute('SELECT * FROM tns LIMIT 0')
            break
        except (psycopg2.OperationalError, psycopg2.ProgrammingError):
            logging.info('Waiting postgress to be available')
            sleep(1)

    logging.warning('POSTGRES IS AVAILABLE')


if __name__ == '__main__':
    main()
