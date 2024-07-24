from fastapi import FastAPI
from routes.route import router

app = FastAPI()

app.include_router(router)


#----------TEST---------
# from pymongo.mongo_client import MongoClient
# uri = "mongodb+srv://kekelidiane:Di%40Mongo4852@cluster0.ijjxn8g.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# #New Client
# client = MongoClient(uri)

# #Send a ping to confirm a successfull connection
# try:
#     client.admin.command('ping')
#     print("Successfully connected to MongoDB !")
# except Exception as e:
#     print(e)