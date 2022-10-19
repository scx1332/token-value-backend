import logging
from datetime import datetime

import batch_rpc_provider
from batch_rpc_provider import BatchRpcProvider
from sqlalchemy.future import select

import db
import model
import config
from db_queries import db_get_block, db_get_block_date
from db_setup import db_setup
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


async def fill_block_dates(p: BatchRpcProvider):
    chain_id = await p.get_chain_id()

    latest_block = await db_get_block(chain_id=chain_id, latest=True)
    if latest_block is None:
        raise Exception("latest_block is None")
    ct = latest_block.block_timestamp

    # round date down to full minute
    start_time = datetime(ct.year, ct.month, ct.day, ct.hour, ct.minute)

    oldest_block = await db_get_block(chain_id=chain_id, oldest=True)
    if oldest_block is None:
        raise Exception("oldest_block is None")
    ct = oldest_block.block_timestamp

    # round date up to full minute
    end_time = datetime(ct.year, ct.month, ct.day, ct.hour, ct.minute) + timedelta(minutes=1)

    latest_block_date = await db_get_block_date(chain_id=chain_id, latest=True)
    oldest_block_date = await db_get_block_date(chain_id=chain_id, oldest=True)

    time_step = timedelta(minutes=1)

    if latest_block_date and oldest_block_date:
        # fill dates from the latest block up to the latest entry in db
        dates_to_process_at_front = []
        for curr_dt in date_span_generator(start_time, latest_block_date.base_date, delta=time_step):
            dates_to_process_at_front.append(curr_dt)

        # fill dates from the oldest entry in db up to the oldest block
        dates_to_process_at_back = []
        for curr_dt in date_span_generator(oldest_block_date.base_date - time_step, end_time, delta=time_step):
            dates_to_process_at_back.append(curr_dt)
        dates_to_process = dates_to_process_at_front + dates_to_process_at_back
    else:
        # no entries in db, fill all dates
        dates_to_process = []
        for curr_dt in date_span_generator(start_time, end_time, delta=time_step):
            dates_to_process.append(curr_dt)

    if not dates_to_process:
        logger.info(f"No new dates to process")
        return

    logger.info("Generating date span:" + str(start_time) + " - " + str(end_time))

    for curr_dt in dates_to_process:
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
    await db_setup()
    await fill_block_dates()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
