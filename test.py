import asyncio
import json
import platform

import batch_rpc_provider
from aiohttp import web
from sqlalchemy.future import select

import db
import model
from model import TokenERC20Entry
from db import db_engine
from sqlalchemy import create_engine
import batch_rpc_provider
from itertools import groupby

def encode_list(s_list):
    return [[len(list(group)), key] for key, group in groupby(s_list)]


async def find_token_erc20(address, token, block_start, block_every):
    async with db.async_session() as session:
        result = await session.execute(
            select(TokenERC20Entry)
            .filter(TokenERC20Entry.address == address)
            .filter(TokenERC20Entry.token == token)
            .filter(TokenERC20Entry.block_start == block_start)
            .filter(TokenERC20Entry.block_every == block_every)
        )

        return result.scalars().first()


async def main():
    model.BaseClass.metadata.create_all(db_engine)
    p = batch_rpc_provider.BatchRpcProvider("https://polygon-rpc.com", 100)
    min_block = 30000000
    max_block = 30000010
    every_block = 1
    holder = "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245"
    address = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
    print(find_token_erc20(address, holder, min_block, every_block))
    blocks = []
    block_no = min_block
    while block_no < max_block:
        blocks.append(f"0x{block_no:x}")
        block_no += every_block

    balances = await p.get_erc20_balance_history(holder, address, blocks)
    balances_int = [int(x, 0) for x in balances if x is not None]
    print(balances_int)

    token_erc20_entry = TokenERC20Entry()
    token_erc20_entry.block_start = min_block
    token_erc20_entry.block_num = len(blocks)
    token_erc20_entry.block_every = every_block
    token_erc20_entry.token = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
    token_erc20_entry.address = "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245"
    rle_representation = encode_list(balances_int)
    rle_str = json.dumps(rle_representation)
    plain_str = json.dumps(balances_int)

    token_erc20_entry.data = rle_str if len(rle_str) < len(plain_str) else plain_str

    async with db.async_session() as session:
        session.add(token_erc20_entry)
        #result = await session.execute(
        #    insert(model.DaoRequest).values(req)
        #)
        await session.commit()



if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
