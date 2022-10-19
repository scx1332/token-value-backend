import logging

from sqlalchemy.future import select

import db
import model
from model import ChainInfo

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def setup_chain_ids():
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


async def db_setup():
    model.BaseClass.metadata.create_all(db.db_engine)
    await setup_chain_ids()
