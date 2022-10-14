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


@routes.get('/history/{min_block}/{max_block}')
async def history(request):
    # with Session(db_engine) as session:
    #     res = session.query(PathInfoEntry).all()
    p = batch_rpc_provider.BatchRpcProvider("https://polygon-rpc.com", 100)

    min_block = int(request.match_info['min_block'])
    max_block = int(request.match_info['max_block'])
    every_block = 100
    blocks = []
    block_no = min_block
    max_blocks = 100
    while block_no < max_block:
        if len(blocks) >= max_blocks:
            break
        blocks.append(f"0x{block_no:x}")
        block_no += every_block

    balances = await p.get_erc20_balance_history(CHECK_USD_HOLDER, POLYGON_USD_TOKEN, blocks)

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
