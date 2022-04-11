from pymongo import MongoClient
import os


def get_collection(collection_name):
    """Return collection from local DB"""
    client = MongoClient(
        os.environ['DB_URL'],
    )
    mydb = client[collection_name]
    collection = mydb.users
    return collection


def get_column(collection, user, column):
    """Retrieves column list from given collection and user"""
    doc_obj = collection.find_one({"_id": user}, {column: 1, "_id": 0})
    list_data = doc_obj[column]
    return list_data


def update_from_obj(collection, user, obj):
    """Update document of user given object"""
    collection.update_one({"_id": user}, {"$set": obj})
