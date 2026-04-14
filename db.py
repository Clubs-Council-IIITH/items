"""
MongoDB Initialization Module.

This module sets up the connection to the MongoDB database.
It ensures that the required indexes are created.

Attributes:
    MONGO_USERNAME (str): An environment variable having MongoDB username.
                          Defaults to "username".
    MONGO_PASSWORD (str): An environment variable having MongoDB password.
                          Defaults to "password".
    MONGO_PORT (str): MongoDB port. Defaults to "27017".
    MONGO_URI (str): MongoDB URI.
    MONGO_DATABASE (str): MongoDB database name.
    client (pymongo.AsyncMongoClient): MongoDB async client.
    db (pymongo.asynchronous.database.AsyncDatabase): MongoDB database.
    itemsdb (pymongo.asynchronous.collection.AsyncCollection): MongoDB
                                                             items collection.
"""

from os import getenv

from pymongo import AsyncMongoClient

# get mongodb URI and database name from environment variale
MONGO_URI = "mongodb://{}:{}@mongo:{}/".format(
    getenv("MONGO_USERNAME", default="username"),
    getenv("MONGO_PASSWORD", default="password"),
    getenv("MONGO_PORT", default="27017"),
)
MONGO_DATABASE = getenv("MONGO_DATABASE", default="default")

# instantiate mongo client
client = AsyncMongoClient(MONGO_URI)

# get database
db = client[MONGO_DATABASE]
itemsdb = db.items


async def ensure_items_index():
    try:
        indexes = await itemsdb.index_information()
        if "unique_items" in indexes:
            print("The items index exists.")
        else:
            await itemsdb.create_index(
                [("iid", 1)], unique=True, name="unique_items"
            )
            print("The items index was created.")
        print(await itemsdb.index_information())
    except Exception:
        pass
