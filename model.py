import json
from enum import Enum

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import declarative_base


BaseClass = declarative_base()


class SerializationMode(Enum):
    FULL = 1
    MINIMAL = 2


class ChainInfo(BaseClass):
    __tablename__ = "chain_info"
    chain_id = Column(Integer, unique=True, primary_key=True)
    name = Column(String, nullable=False)


class BlockInfo(BaseClass):
    __tablename__ = "block_info"
    id = Column(Integer, primary_key=True)
    chain_id = Column(Integer, ForeignKey("chain_info.chain_id"), nullable=False)
    block_number = Column(Integer, nullable=False)
    block_hash = Column(String, nullable=False)
    block_timestamp = Column(DateTime, nullable=False)
    number_of_transactions = Column(Integer, nullable=False)


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
        if isinstance(obj, PathInfoEntry):
            return obj.to_json(mode=self._mode)
        return super().default(obj)


if __name__ == "__main__":
    pi1 = PathInfoEntry(path_info=1, files_checked=2, files_failed=3, total_size=4)
    pi2 = PathInfoEntry(path_info=10, files_checked=11, files_failed=12, total_size=13)

    print(json.dumps([pi1, pi2], cls=LocalJSONEncoder, indent=4, mode=SerializationMode.MINIMAL))
    print(json.dumps([pi1, pi2], cls=LocalJSONEncoder, indent=4, mode=SerializationMode.FULL))

