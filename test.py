import asyncio

from aiohttp import web

import model
from model import TokenERC20Entry
from db import db_engine
from sqlalchemy import create_engine


async def main():
    model.BaseClass.metadata.create_all(db_engine)


if __name__ == "__main__":
    asyncio.run(main())