from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError

from config import DATABASE_NAME, MONGO_URI


def get_mongo_client(uri: str = MONGO_URI) -> MongoClient:
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError) as exc:
        raise RuntimeError(f"Khong ket noi duoc MongoDB: {exc}") from exc


def get_database(client: MongoClient):
    return client[DATABASE_NAME]
