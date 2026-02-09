from pymongo import MongoClient

def init_mongo_database():
    #client = MongoClient("mongodb://localhost:27017/")
    client = MongoClient("mongodb://admin:admin@mongodb:27017/")

    db = client["event_manager"]  
    print("Connected to MongoDB local")
    return db

mongo_db = init_mongo_database()

"""
import os 
import time from pymongo 
import MongoClient, errors 
MONGO_HOST = os.getenv("MONGO_HOST", "localhost") 
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017)) 
MONGO_USER = os.getenv("MONGO_USER", "myappuser") 
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "local_password") 
MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "local_password") 
MONGO_DB = os.getenv("MONGO_DB", "demo_database") 
def init_mongo_database(): 
    retries = 5 
    delay = 5 
    for _ in range(retries): 
        try: 
            client = MongoClient( 
            MONGO_HOST, 
            MONGO_PORT, 
            username=MONGO_USER, 
            password=MONGO_INITDB_ROOT_PASSWORD, 
            authSource="admin", #MONGO_DB, 
            serverSelectionTimeoutMS=5000 ) 
            client.admin.command('ping') 
            print("Connected to MongoDB") 
            return client[MONGO_DB] 
        except errors.ServerSelectionTimeoutError as _: 
            print(f"MongoDB not ready yet, retrying in {delay} seconds...") 
            time.sleep(delay) 
            raise errors.ConnectionFailure("Could not connect to MongoDB after several attempts") 
"""