import logging
from datetime import datetime

import batch_rpc_provider
from sqlalchemy.future import select

import db
import model
import config
from db_setup import db_setup
from fill_block_dates import fill_block_dates
from model import BlockInfo, ChainInfo, BlockDate

from datetime import date, datetime, timedelta

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def fill_blocks(p: batch_rpc_provider.BatchRpcProvider, blocks_at_once=10000):
    logger.info(f"Starting fill_blocks... with provider {config.POLYGON_PROVIDER_URL}")



    chain_id = await p.get_chain_id()

    latest_block = await p.get_latest_block()

    logger.info(f"Get block info from DB...")

    async with db.async_session() as session:
        result = await session.execute(
            select(BlockInfo.block_number)
                .filter(BlockInfo.chain_id == chain_id)
        )
        blocks_in_db = set(result.scalars().all())

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
            await fill_blocks(config.FILL_BLOCKS_AT_ONCE)
        except Exception as e:
            print(f"Error: {e}")

        secs = 5
        print(f"Loop finished, sleeping for {secs} seconds")
        # await fill_block_dates()
        await asyncio.sleep(secs)


async def main():
    logging.getLogger("batch_rpc_provider.batch_rpc_provider").setLevel(logging.WARNING)

    await db_setup()
    await fill_blocks_loop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
