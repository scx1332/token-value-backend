import logging
from datetime import datetime

import batch_rpc_provider
from sqlalchemy.future import select

import db
import model
import config
from model import BlockInfo, ChainInfo, BlockDate

from datetime import date, datetime, timedelta

def datespan(startDate, endDate, delta=timedelta(days=1)):
    currentDate = startDate
    while currentDate > endDate:
        yield currentDate
        currentDate -= delta

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def fill_blocks():
    p = batch_rpc_provider.BatchRpcProvider(config.POLYGON_PROVIDER_URL, 100)


    async with db.async_session() as session:
        result = await session.execute(
            select(ChainInfo)
                .filter(ChainInfo.chain_id == 137)
        )
        if result.scalars().first() is None:
            ci = ChainInfo()
            ci.chain_id = 137
            ci.name = "Polygon"
            session.add(ci)
            await session.commit()



    latest_block = await p.get_latest_block()

    async with db.async_session() as session:
        result = await session.execute(
            select(BlockInfo)
                .filter(BlockInfo.chain_id == 137)
        )
        list = result.scalars()


    blocks_in_db = set()
    for block in list:
        blocks_in_db.add(block.block_number)

    blocks = set()
    i = 0
    while latest_block - i > 0:
        block_num = latest_block - i
        i += 1
        if block_num in blocks_in_db:
            continue
        blocks.add(block_num)
        logger.debug(f"Added block num: {block_num}")
        if len(blocks) >= 1000:
            break

    try:
        blocks = await p.get_blocks_by_numbers(blocks, False)
        async with db.async_session() as session:
            for block in blocks:
                block_info = BlockInfo()
                block_info.chain_id = 137
                block_info.block_number = int(block["number"], 0)
                block_info.block_hash = block["hash"]
                block_info.block_timestamp = datetime.fromtimestamp(int(block["timestamp"], 0))
                block_info.number_of_transactions = len(block["transactions"])
                session.add(block_info)
            await session.commit()
    except Exception as e:
        print(f"Error: {e}")


async def fill_block_dates():
    chain_id = 137
    ct = datetime.now()
    start_time = datetime(ct.year, ct.month, ct.day, ct.hour, ct.minute)
    end_time = start_time - timedelta(days=1)

    for day in datespan(start_time, end_time, delta=timedelta(minutes=1)):
        async with db.async_session() as session:
            result = await session.execute(
                select(BlockDate)
                    .filter(BlockDate.base_date == day)
                    .filter(BlockDate.chain_id == chain_id)
            )
            if result.scalars().first():
                print(f"Skipping {day}")
                continue

            result = await session.execute(
                select(BlockInfo)
                    .filter(BlockInfo.block_timestamp > day - timedelta(minutes=1))
                    .filter(BlockInfo.block_timestamp <= day)
                    .order_by(BlockInfo.block_timestamp.asc())
            )
            list = result.scalars()
            last = None
            for l in list:
                last = l
            if last:
                print(f"Last block for {day} is {last.block_timestamp}")
                bd = BlockDate()
                bd.chain_id = chain_id
                bd.base_date = day
                bd.block_number = last.block_number
                bd.block_date = last.block_timestamp
                session.add(bd)
                await session.commit()




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