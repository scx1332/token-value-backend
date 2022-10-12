from flask import Flask, render_template, url_for
from flask_cors import CORS, cross_origin
from flask import request
import json
import os
import shutil
import argparse
import logging
from sqlalchemy.orm import declarative_base, Session, relationship, scoped_session

from model import PathInfo, BaseClass, PathInfoEntry, LocalJSONEncoder, SerializationMode
from db import db_engine

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser(description='Erigon monitor params')
parser.add_argument('--db', dest="db", type=str, help='sqlite or postgres', default="sqlite")
parser.add_argument('--host', dest="host", type=str, help='Host name', default="127.0.0.1")
parser.add_argument('--config-path', dest="config_path", type=str, help='Config path', default="./config.json")
parser.add_argument('--port', dest="port", type=int, help='Port number', default="5000")
parser.set_defaults(dumpjournal=True)

args = parser.parse_args()

app = Flask(__name__)
cors = CORS(app)


@app.route('/')
def hello():
    print("test")
    return 'Hello, World!'


@app.route('/html')
def html():
    return render_template('plot.html', sizes_url=url_for("sizes"))


@app.route('/htmltest')
def htmltest():
    return render_template('plot.html', sizes_url="http://51.38.53.113:5000/sizes")


@app.route('/sizes')
@cross_origin()
def sizes():
    with Session(db_engine) as session:
        res = session.query(PathInfoEntry).all()
    resp = app.response_class(
        response=json.dumps(res, cls=LocalJSONEncoder, mode=SerializationMode.FULL),
        status=200,
        mimetype='application/json'
    )
    return resp


def main():
    BaseClass.metadata.create_all(db_engine)
    app.run(host=args.host, port=args.port, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
