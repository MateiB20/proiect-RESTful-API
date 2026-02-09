#from app.databases.mongo_db import init_mongo_database

#mongo_db = init_mongo_database()
from peewee import SqliteDatabase, Model , CharField , IntegerField , ForeignKeyField , CompositeKey
db = SqliteDatabase("event_manager.db")
