from pymongo import MongoClient

client = MongoClient("mongodb+srv://kekelidiane:Di%40Mongo4852@cluster0.ijjxn8g.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

db = client.item_db

collection_name = db["item_collection"]
 




