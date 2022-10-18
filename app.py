import asyncio
import json
import os
import shutil
import argparse
import logging
from datetime import datetime, timedelta

import batch_rpc_provider
from aiohttp import web

from sqlalchemy.orm import declarative_base, Session, relationship, scoped_session

import config
from db_queries import db_get_minute_series, db_get_hours_series
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



POLYGON_USD_TOKEN = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
CHECK_USD_HOLDER = "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245"

@routes.get('/minutes')
async def minutes(request):
    current_date = datetime.now()
    old_date = current_date - timedelta(days=1)
    cd = await db_get_minute_series(chain_id=137, start_date=old_date, end_date=current_date)

    res = json.dumps(cd, cls=LocalJSONEncoder, indent=4, mode=SerializationMode.FULL)
    return web.json_response(text=res)


@routes.get('/day/{holder}/{token}')
async def day(request):
    p = batch_rpc_provider.BatchRpcProvider(config.POLYGON_PROVIDER_URL, 100)

    token = request.match_info['token']
    address = request.match_info['holder']

    current_date = datetime.now()
    old_date = current_date - timedelta(days=1)
    cd = await db_get_hours_series(chain_id=137, start_date=old_date, end_date=current_date)
    blocks = [f"0x{x.block_number:x}" for x in cd]
    balances = await p.get_erc20_balance_history(address, token, blocks)

    # balances = [await p.get_erc20_balance(address, token)]
    new_dict = {}
    for balance in balances:
        for k, v in zip(blocks, balances):
            if v == "0x":
                v = 0
            else:
                v = int(v, 0)
            new_dict[int(k, 0)] = v

    # print(res)

    return web.json_response(new_dict, dumps=json.dumps)



@routes.get('/history/{min_block}/{max_block}/{every_block}/{holder}/{token}')
async def history(request):
    # with Session(db_engine) as session:
    #     res = session.query(PathInfoEntry).all()
    p = batch_rpc_provider.BatchRpcProvider(config.POLYGON_PROVIDER_URL, 100)

    min_block = int(request.match_info['min_block'])
    max_block = int(request.match_info['max_block'])
    every_block = int(request.match_info['every_block'])
    token = request.match_info['token']
    address = request.match_info['holder']

    blocks = []
    block_no = min_block
    max_blocks = 100
    while block_no < max_block:
        if len(blocks) >= max_blocks:
            break
        blocks.append(f"0x{block_no:x}")
        block_no += every_block

    balances = await p.get_erc20_balance_history(address, token, blocks)
    # balances = [await p.get_erc20_balance(address, token)]

    new_dict = {}
    for balance in balances:
        for k, v in zip(blocks, balances):
            if v == "0x":
                v = 0
            else:
                v = int(v, 0)
            new_dict[int(k, 0)] = v

    # print(res)

    return web.json_response(new_dict, dumps=json.dumps)


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
