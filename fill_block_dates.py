import logging
from datetime import datetime

import batch_rpc_provider
from sqlalchemy.future import select

import db
import model
import config
from db_queries import db_get_block
from model import BlockInfo, ChainInfo, BlockDate

from datetime import date, datetime, timedelta

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def date_span_generator(start_date, end_date, delta=timedelta(days=1)):
    current_date = start_date
    while current_date > end_date:
        yield current_date
        current_date -= delta


async def fill_block_dates():
    chain_id = 137

    latest_block = await db_get_block(chain_id=chain_id, latest=True)
    if latest_block is None:
        raise Exception("latest_block is None")
    ct = latest_block.block_timestamp

    start_time = datetime(ct.year, ct.month, ct.day, ct.hour, ct.minute)

    oldest_block = await db_get_block(chain_id=chain_id, oldest=True)
    if oldest_block is None:
        raise Exception("oldest_block is None")
    ct = oldest_block.block_timestamp

    end_time = datetime(ct.year, ct.month, ct.day, ct.hour, ct.minute)

    print("Generating date span:" + str(start_time) + " - " + str(end_time))

    for curr_dt in date_span_generator(start_time, end_time, delta=timedelta(minutes=1)):
        async with db.async_session() as session:
            result = await session.execute(
                select(BlockDate)
                    .filter(BlockDate.base_date == curr_dt)
                    .filter(BlockDate.chain_id == chain_id)
            )
            if result.scalars().first():
                print(f"Skipping {curr_dt}")
                continue

            result = await session.execute(
                select(BlockInfo)
                    .filter(BlockInfo.block_timestamp > curr_dt - timedelta(minutes=1))
                    .filter(BlockInfo.block_timestamp <= curr_dt)
                    .order_by(BlockInfo.block_timestamp.asc())
            )
            list = result.scalars()
            last = None
            for l in list:
                last = l
            if last:
                print(f"Last block for {curr_dt} is {last.block_timestamp}")
                bd = BlockDate()
                bd.chain_id = chain_id
                bd.base_date = curr_dt
                bd.block_number = last.block_number
                bd.block_date = last.block_timestamp
                bd.base_minute = curr_dt.minute
                bd.base_hour = curr_dt.hour
                session.add(bd)
                await session.commit()


async def main():
    model.BaseClass.metadata.create_all(db.db_engine)
    await fill_block_dates()

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())