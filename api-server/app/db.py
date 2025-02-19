import os
from pymongo import MongoClient

# Use environment variable with a fallback to internal service name
mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
client = MongoClient(mongo_uri)
db = client.get_database("your_database_name")