import os
from pymongo import MongoClient

# Use environment variable with a fallback to internal service name
mongo_uri = os.getenv("MONGO_URI", "mongodb:27017")
mongo_username = os.getenv("MONGO_USERNAME", "root")
mongo_password = os.getenv("MONGO_PASSWORD", "root")
mongo_dbname = os.getenv("MONGO_DBNAME", "observationsdb")
client = MongoClient(f"mongodb://{mongo_username}:{mongo_password}@{mongo_uri}")
db = client.get_database(mongo_dbname)