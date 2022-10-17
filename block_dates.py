from sqlalchemy.future import select

import db
import model

async def analyze_block_gaps():
    async with db.async_session() as session:
        result = await session.execute(
            select(model.BlockInfo)
                .filter(model.BlockInfo.chain_id == 137)
                .order_by(model.BlockInfo.block_number)
        )
        list = result.scalars()
        prev = None
        for l in list:

            if isinstance(l, model.BlockInfo) and isinstance(prev, model.BlockInfo):
                if l.block_number - prev.block_number != 1:
                    print(f"Gap between {prev.block_number} and {l.block_number} not equal to one")
                gap_seconds = (l.block_timestamp - prev.block_timestamp).seconds
                if gap_seconds > 10:
                    print(f"Gap {l.block_number}: {gap_seconds} seconds")
            prev = l




async def analyze_gaps():
    async with db.async_session() as session:
        result = await session.execute(
            select(model.BlockDate)
                .filter(model.BlockDate.chain_id == 137)
        )
        list = result.scalars()

        list = [f for f in list]

        for gap in list:
            if isinstance(gap, model.BlockDate):
                diff = gap.base_date - gap.block_date
                if diff.seconds > 1:
                    await session.delete(gap)
                    print(gap.block_number)

        await session.commit()
    print(len(list))

async def main():
    await analyze_block_gaps()

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())