#!/usr/bin/env python3

import psycopg2
from time import sleep


def main():
    while True:
        try:
            with psycopg2.connect(host='tns-catalog-sql', user='app', dbname='catalog') as con:
                with con.cursor() as cur:
                    cur.execute('SELECT * FROM tns LIMIT 0')
            break
        except (psycopg2.OperationalError, psycopg2.ProgrammingError):
            print('Waiting postgress to be available')
            sleep(1)
            pass

    print('POSTGRES IS AVAILABLE')


if __name__ == '__main__':
    main()
