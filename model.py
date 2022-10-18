import json
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, UniqueConstraint, PrimaryKeyConstraint, \
    ForeignKeyConstraint
from sqlalchemy.orm import declarative_base


BaseClass = declarative_base()


class SerializationMode(Enum):
    FULL = 1
    MINIMAL = 2


class ChainInfo(BaseClass):
    __tablename__ = "chain_info"
    chain_id = Column(Integer, unique=True, primary_key=True)
    name = Column(String, nullable=False)


class BlockDate(BaseClass):
    __tablename__ = "block_date"
    __table_args__ = (
        # this can be db.PrimaryKeyConstraint if you want it to be a primary key
        PrimaryKeyConstraint('chain_id', 'base_date'),
        ForeignKeyConstraint(
            ["block_number", "chain_id"],
            ["block_info.block_number", "block_info.chain_id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        )
    )
    chain_id = Column(Integer, ForeignKey("chain_info.chain_id"), nullable=False)
    base_date = Column(DateTime, nullable=False, index=True)
    block_number = Column(Integer, nullable=False)
    block_date = Column(DateTime, nullable=False)
    base_hour = Column(Integer, nullable=False, index=True)
    base_minute = Column(Integer, nullable=False, index=True)

    def to_json(self, mode=SerializationMode.FULL):
        if mode == SerializationMode.FULL:
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}
        elif mode == SerializationMode.MINIMAL:
            return {
                "block_number": self.block_number
            }
        else:
            raise Exception(f"Unknown mode {mode}")


class BlockInfo(BaseClass):
    __tablename__ = "block_info"
    __table_args__ = (
        # this can be db.PrimaryKeyConstraint if you want it to be a primary key
        PrimaryKeyConstraint('chain_id', 'block_number'),
    )

    chain_id = Column(Integer, ForeignKey("chain_info.chain_id"), nullable=False)
    block_number = Column(Integer, index=True, nullable=False)
    block_hash = Column(String, nullable=False)
    block_timestamp = Column(DateTime, index=True, nullable=False)
    number_of_transactions = Column(Integer, index=True, nullable=False)

    def to_json(self, mode=SerializationMode.FULL):
        if mode == SerializationMode.FULL:
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}
        elif mode == SerializationMode.MINIMAL:
            return {
                "block_number": self.block_number
            }
        else:
            raise Exception(f"Unknown mode {mode}")


class TokenERC20Entry(BaseClass):
    __tablename__ = "token_erc20_entry"
    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    token = Column(String, nullable=False)
    block_start = Column(Integer, nullable=False)
    block_num = Column(Integer, nullable=False)
    block_every = Column(Integer, nullable=False)
    data = Column(String, nullable=False)

    def to_json(self, mode=SerializationMode.FULL):
        if mode == SerializationMode.FULL:
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}
        elif mode == SerializationMode.MINIMAL:
            return {
                "block_every": self.block_every
            }
        else:
            raise Exception(f"Unknown mode {mode}")


class LocalJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        self._mode = kwargs.pop('mode') if 'mode' in kwargs else None
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, BlockInfo):
            return obj.to_json(mode=self._mode)
        if isinstance(obj, BlockDate):
            return obj.to_json(mode=self._mode)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


if __name__ == "__main__":
    # pi1 = PathInfoEntry(path_info=1, files_checked=2, files_failed=3, total_size=4)
    # pi2 = PathInfoEntry(path_info=10, files_checked=11, files_failed=12, total_size=13)

    # print(json.dumps([pi1, pi2], cls=LocalJSONEncoder, indent=4, mode=SerializationMode.MINIMAL))
    # print(json.dumps([pi1, pi2], cls=LocalJSONEncoder, indent=4, mode=SerializationMode.FULL))
    pass

