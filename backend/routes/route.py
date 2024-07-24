from fastapi import APIRouter
from models.items import Item
from config.database import collection_name
from schema.schemas import list_serial
from bson import ObjectId

router = APIRouter()

#GET request method
@router.get('/')
async def get_items():
    items = list_serial(collection_name.find())
    return items

#POST request method
@router.post("/")
async def post_items(item: Item):
    collection_name.insert_one(dict(item))

#PUT request method
@router.put("/{id}")
async def put_items(id: str, item: Item):
    collection_name.find_one_and_update({"_id": ObjectId(id)}, {"$set": dict(item)})

#DELETE request method
@router.delete("/{id}")
async def delete_items(id: str):
    collection_name.find_one_and_delete({"_id": ObjectId(id)})
