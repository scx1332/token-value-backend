from sqlalchemy.future import select

import db
from model import BlockInfo, BlockDate
from sqlalchemy.sql import func

async def db_get_minute_series(chain_id, start_date, end_date):
    async with db.async_session() as session:
        result = await session.execute(
            select(BlockDate)
                .filter(BlockDate.chain_id == chain_id)
                .filter(BlockDate.base_date >= start_date)
                .filter(BlockDate.base_date <= end_date)
                .order_by(BlockDate.block_number)
        )
        return result.scalars().all()


async def db_get_hours_series(chain_id, start_date, end_date):
    async with db.async_session() as session:
        result = await session.execute(
            select(BlockDate)
                .filter(BlockDate.chain_id == chain_id)
                .filter(BlockDate.base_date >= start_date)
                .filter(BlockDate.base_date <= end_date)
                .filter(BlockDate.base_minute == 0)
                .order_by(BlockDate.block_number)
        )
        return result.scalars().all()


async def db_get_day_series(chain_id, start_date, end_date):
    async with db.async_session() as session:
        result = await session.execute(
            select(BlockDate)
                .filter(BlockDate.chain_id == chain_id)
                .filter(BlockDate.base_date >= start_date)
                .filter(BlockDate.base_date <= end_date)
                .filter(BlockDate.base_minute == 0)
                .order_by(BlockDate.block_number)
        )
        return result.scalars().all()


async def db_get_block(chain_id, latest=False, oldest=False) -> BlockInfo:
    if chain_id is None:
        raise Exception("chain_id is None")
    if latest and oldest:
        raise Exception("latest and oldest are both True")
    if not latest and not oldest:
        raise Exception("latest and oldest are both False")
    if latest:
        order_by_method = BlockInfo.block_number.desc()
    else:
        order_by_method = BlockInfo.block_number.asc()

    async with db.async_session() as session:
        result = await session.execute(
            select(BlockInfo)
                .filter(BlockInfo.chain_id == chain_id)
                .order_by(order_by_method)
                .limit(1)
        )
        block = result.scalars().first()
        if block is None:
            return None
        return block

