import os

POLYGON_PROVIDER_URL = os.environ.get("POLYGON_PROVIDER", "https://polygon-rpc.com")
ETHEREUM_PROVIDER_URL = os.environ.get("ETHEREUM_PROVIDER", "https://geth.golem.network:55555")

FILL_BLOCKS_AT_ONCE = int(os.environ.get("FILL_BLOCKS_AT_ONCE", "1000"))
