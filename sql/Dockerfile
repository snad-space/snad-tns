ARG PSQL_VERSION=15
FROM postgres:${PSQL_VERSION}-bullseye
ARG PSQL_VERSION=15

RUN apt-get update &&\
    apt-get install -y postgresql-server-dev-${PSQL_VERSION} tar gzip make gcc g++ libhealpix-dev libhealpix-cxx-dev libchealpix-dev pkg-config python3 python3-pip

ADD https://github.com/postgrespro/pgsphere/archive/master.tar.gz pgsphere-master.tar.gz
RUN tar -zxf pgsphere-master.tar.gz && \
	cd pgsphere-master && \
	make USE_PGXS=1 PG_CONFIG=/usr/bin/pg_config && \
	make USE_PGXS=1 PG_CONFIG=/usr/bin/pg_config install && \
	cd .. && \
	rm -rf pgsphere-master pgsphere-master.tar.gz

COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

COPY docker-entrypoint-initdb.d/* /docker-entrypoint-initdb.d/
COPY fill_table.py /fill_table.py

# Required for upgrade container
COPY docker-entrypoint-upgrade.sh /docker-entrypoint-upgrade.sh

ENV POSTGRES_HOST_AUTH_METHOD trust
ENV PYTHONUNBUFFERED 0
