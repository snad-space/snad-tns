from __future__ import annotations

import json
import math as m
from dataclasses import dataclass
from functools import partial

from aiohttp.web import Application, Response, json_response, RouteTableDef, Request, HTTPBadRequest
from asyncpg import create_pool, Connection, BitString

MAX_RADIUS_DEG = 1.0
MAX_RADIUS_ARCSEC = 3600.0 * MAX_RADIUS_DEG


routes = RouteTableDef()


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BitString):
            return obj.to_int()
        if isinstance(obj, SPoint):
            return obj.to_dict()
        return super().default(obj)


json_response = partial(json_response, dumps=partial(json.dumps, cls=JSONEncoder))


@dataclass
class SPoint:
    ra: float
    dec: float

    @property
    def ra_rad(self) -> float:
        return m.radians(self.ra)

    @property
    def dec_rad(self) -> float:
        return m.radians(self.dec)

    def to_sql(self) -> str:
        return f'({self.ra_rad}, {self.dec_rad})'

    @staticmethod
    def from_sql(s) -> SPoint:
        s = s.strip('()')
        ra, dec = (m.degrees(float(x)) for x in s.split(','))
        return SPoint(ra=ra, dec=dec)

    def to_dict(self) -> dict:
        return {'ra': self.ra, 'dec': self.dec}


@dataclass
class SCircle:
    point: SPoint
    radius: float

    @property
    def radius_rad(self) -> float:
        return m.radians(self.radius / 3600.)

    def to_sql(self) -> str:
        return f'<{self.point.to_sql()}, {self.radius_rad}>'

    @staticmethod
    def from_sql(s) -> SCircle:
        s = s.strip('<>')
        point, radius = s.rsplit(',', maxsplit=1)
        point = SPoint.from_sql(point)
        radius = m.degrees(float(radius)) * 3600.
        return SCircle(point=point, radius=radius)


@routes.get('/')
async def index(_) -> Response:
    return Response(
        text='''
            <p>
                Welcome to <a href="//snad.space">SNAD</a>
                <a href="http://www.wis-tns.org">TNS</a>
                mirror
            </p>
            <p>
                See API details on <a href="/api/v1/help">/api/v1/help</a>
            </p>
            <p>
                See source code <a href="https://github.com/snad-space/snad-tns">on GitHub</a>
            </p>
        ''',
        content_type='text/html',
    )


@routes.get('/api/v1/help')
async def help(_) -> Response:
    return Response(
        text=f'''
            <h1>Available resources</h1>
            <h2><font face='monospace'>/api/v1/all</font></h2>
                <p> Get all objects</p>
            <h2><font face='monospace'>/api/v1/circle</font></h2>
                <p> Get objects in the circle</p>
                <p> Query parameters:</p>
                <ul>
                    <li><font face='monospace'>ra</font> &mdash; right ascension of the circle center, degrees. Mandatory</li>
                    <li><font face='monospace'>dec</font> &mdash; declination of the circle center, degrees. Mandatory</li>
                    <li><font face='monospace'>radius_arcsec</font> &mdash; circle radius, arcseconds. Mandatory, should be positive and less than {MAX_RADIUS_ARCSEC}</li>
                </ul>
            <h2><font face='monospace'>/api/v1/object</font></h2>
                <p> Get object by name</p>
                <p> Query parameters:</p>
                <ul>
                    <li><font face='monospace'>name</font> &mdash; name of the event, like "2018lwh". Mandatory</li>
                </ul>
        ''',
        content_type='text/html',
    )


def ra_dec_radius_from_request(request: Request, max_radius: float) -> Tuple[float, float, float]:
    try:
        ra = float(request.query['ra'])
        dec = float(request.query['dec'])
        radius = float(request.query['radius_arcsec'])
    except KeyError:
        raise HTTPBadRequest(reason='All of "ra", "dec" and "radius_arcsec" fields should be specified')
    except ValueError:
        raise HTTPBadRequest(reason='All or "ra", "dec" and "radius_arcsec" fields should be floats')
    if radius <= 0 or radius > max_radius:
        raise HTTPBadRequest(reason=f'"radius" should be positive and less than {max_radius}')
    return ra, dec, radius


@routes.get('/api/v1/circle')
async def select_in_circle(request: Request) -> Response:
    ra, dec, radius = ra_dec_radius_from_request(request, max_radius=MAX_RADIUS_ARCSEC)

    circle = SCircle(point=SPoint(ra=ra, dec=dec), radius=radius)

    async with request.app['pg_pool'].acquire() as con:
        data = await con.fetch(
            f'''
            SELECT *
            FROM tns
            WHERE coord @ ${1}::scircle
            ''',
            circle,
        )
    data = [dict(row) for row in data]
    return json_response(data)


@routes.get('/api/v1/object')
async def select_object(request: Request) -> Response:
    try:
        name = request.query['name']
    except KeyError:
        raise HTTPBadRequest(reason='"name" field should be specified')
    # Name should be unique, but I wouldn't like to make this column UNIQUE and fail at DB creation time
    async with request.app['pg_pool'].acquire() as con:
        data = await con.fetch(
            f'''
            SELECT *
            FROM tns
            WHERE name = ${1}
            LIMIT 1
            ''',
            name,
        )
    row = dict(data[0])
    return json_response(row)


@routes.get('/api/v1/all')
async def select_all(request: Request) -> Response:
    async with request.app['pg_pool'].acquire() as con:
        data = await con.fetch(
            f'''
            SELECT *
            FROM tns
            ''',
        )
    data = [dict(row) for row in data]
    return json_response(data)


async def connection_setup(con: Connection):
    await con.set_type_codec(
        'spoint',
        encoder=SPoint.to_sql,
        decoder=SPoint.from_sql,
        format='text',
    )
    await con.set_type_codec(
        'scircle',
        encoder=SCircle.to_sql,
        decoder=SCircle.from_sql,
        format='text',
    )


async def on_startup(app: Application):
    app['pg_pool'] = await create_pool(host='tns-catalog-sql', database='catalog', user='app', setup=connection_setup)


async def on_cleanup(app: Application):
    await app['pg_pool'].close()


async def get_app():
    app = Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.add_routes(routes)
    return app
