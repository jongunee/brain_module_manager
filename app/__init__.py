from flask import Flask
from .routes import bp
from config import load_db_info
from pymongo.mongo_client import MongoClient


def create_app():
    app = Flask(__name__)

    db_uri, db_name, db_collection_metadata, db_collection_modeldata = load_db_info()
    mongo_client = MongoClient(db_uri)
    app.db_metadata = mongo_client[db_name][db_collection_metadata]
    app.db_modeldata = mongo_client[db_name][db_collection_modeldata]

    app.register_blueprint(bp)
    return app
