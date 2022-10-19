import logging

from batch_rpc_provider import BatchRpcProvider

import config
import db
import model
from db_setup import db_setup
from fill_block_dates import fill_block_dates
from fill_blocks import fill_blocks


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def bg_work_loop(p: BatchRpcProvider):
    while True:
        try:
            await fill_blocks(p, config.FILL_BLOCKS_AT_ONCE)
            await fill_block_dates(p)
        except Exception as e:
            print(f"Error: {e}")

        secs = 5
        logger.info(f"Loop finished, sleeping for {secs} seconds")
        await asyncio.sleep(secs)


async def main():
    logging.getLogger("batch_rpc_provider.batch_rpc_provider").setLevel(logging.WARNING)
    p = BatchRpcProvider(config.POLYGON_PROVIDER_URL, 100)

    await db_setup()
    await bg_work_loop(p)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())