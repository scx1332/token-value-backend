FROM python:3.9
WORKDIR /runtime

RUN pip install batch-rpc-provider 
RUN pip install sqlalchemy
RUN pip install aiohttp
RUN pip install sqlalchemy_utils
RUN pip install psycopg2
RUN pip install asyncpg




COPY *.py ./
COPY templates ./templates
ENV PATH=".:${PATH}"
