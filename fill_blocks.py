import logging
from datetime import datetime

import batch_rpc_provider
from sqlalchemy.future import select

import db
import model
import config
from model import BlockInfo, ChainInfo, BlockDate

from datetime import date, datetime, timedelta

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.getLogger("batch_rpc_provider.batch_rpc_provider").setLevel(logging.WARNING)

async def fill_blocks(blocks_at_once=10000):
    p = batch_rpc_provider.BatchRpcProvider(config.POLYGON_PROVIDER_URL, 100)
    logger.info(f"Starting fill_blocks... with provider {config.POLYGON_PROVIDER_URL}")

    chains = [{
        "chain_id": 137,
        "name": "Polygon",
    },
        {
            "chain_id": 56,
            "name": "Binance Smart Chain",
        },
        {
            "chain_id": 1,
            "name": "Ethereum",
        }
    ]

    logger.info(f"Filling chain info data...")

    async with db.async_session() as session:
        for chain in chains:
            result = await session.execute(
                select(ChainInfo)
                    .filter(ChainInfo.chain_id == chain["chain_id"])
            )
            if result.scalars().first() is None:
                ci = ChainInfo()
                ci.chain_id = chain["chain_id"]
                ci.name = chain["name"]
                session.add(ci)
                await session.commit()

    chain_id = await p.get_chain_id()

    latest_block = await p.get_latest_block()

    logger.info(f"Get block info from DB...")

    async with db.async_session() as session:
        result = await session.execute(
            select(BlockInfo)
                .filter(BlockInfo.chain_id == chain_id)
        )
        list = result.scalars()

    blocks_in_db = set()
    for block in list:
        blocks_in_db.add(block.block_number)

    logger.info(f"Got {len(blocks_in_db)} from db...")

    logger.info(f"Prepare block list ...")

    blocks = set()
    i = 0
    while latest_block - i > 0:
        block_num = latest_block - i
        i += 1
        if block_num in blocks_in_db:
            continue
        blocks.add(block_num)
        logger.debug(f"Added block num: {block_num}")
        if len(blocks) >= blocks_at_once:
            break


    try:
        logger.info(f"Get blocks info from provider: number of blocks: {len(blocks)}...")

        blocks = await p.get_blocks_by_numbers(blocks, False)

        logger.info(f"Put data into database: number of blocks: {len(blocks)} ...")
        async with db.async_session() as session:
            for block in blocks:
                block_info = BlockInfo()
                block_info.chain_id = chain_id
                block_info.block_number = int(block["number"], 0)
                block_info.block_hash = block["hash"]
                block_info.block_timestamp = datetime.fromtimestamp(int(block["timestamp"], 0))
                block_info.number_of_transactions = len(block["transactions"])
                session.add(block_info)
            await session.commit()
    except Exception as e:
        print(f"Error: {e}")


async def fill_blocks_loop():
    while True:
        try:
            await fill_blocks()
        except Exception as e:
            print(f"Error: {e}")

        secs = 0
        print(f"Loop finished, sleeping for {secs} seconds")
        # await fill_block_dates()
        await asyncio.sleep(secs)


async def main():
    model.BaseClass.metadata.create_all(db.db_engine)
    await fill_blocks_loop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
