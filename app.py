import asyncio
import json
import os
import shutil
import argparse
import logging
import batch_rpc_provider
from aiohttp import web

from sqlalchemy.orm import declarative_base, Session, relationship, scoped_session

from model import BaseClass, LocalJSONEncoder, SerializationMode
from db import db_engine

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser(description='Erigon monitor params')
parser.add_argument('--db', dest="db", type=str, help='sqlite or postgres', default="sqlite")
parser.add_argument('--host', dest="host", type=str, help='Host name', default="127.0.0.1")
parser.add_argument('--config-path', dest="config_path", type=str, help='Config path', default="./config.json")
parser.add_argument('--port', dest="port", type=int, help='Port number', default="5000")
parser.set_defaults(dumpjournal=True)

args = parser.parse_args()


routes = web.RouteTableDef()

@routes.get('/')
async def hello(request):
    print("test")
    return web.Response(text="Hello, world")



@routes.get('/htmltest')
def htmltest():
    return render_template('plot.html', sizes_url="http://51.38.53.113:5000/sizes")


POLYGON_USD_TOKEN = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
CHECK_USD_HOLDER = "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245"


@routes.get('/sizes')
async def sizes(request):
    # with Session(db_engine) as session:
    #     res = session.query(PathInfoEntry).all()
    p = batch_rpc_provider.BatchRpcProvider("https://polygon-rpc.com", 100)

    min_block = 30000000
    max_block = 30000010
    every_block = 1
    blocks = []
    block_no = min_block
    while block_no < max_block:
        blocks.append(f"0x{block_no:x}")
        block_no += every_block

    balances = await p.get_erc20_balance_history(CHECK_USD_HOLDER, POLYGON_USD_TOKEN, blocks)

    return web.json_response(balances, dumps=json.dumps)


    #resp = app.response_class(
    #    response=json.dumps(res, cls=LocalJSONEncoder, mode=SerializationMode.FULL),
    #    status=200,
    #    mimetype='application/json'
    #)
    #return resp


async def main():
    BaseClass.metadata.create_all(db_engine)
    task = asyncio.create_task(
        web._run_app(app, handle_signals=False)  # noqa
    )
    await task

if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host=args.host, port=args.port)