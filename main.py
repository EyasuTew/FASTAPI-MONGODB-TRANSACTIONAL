import uvicorn
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import string

app = FastAPI()

client = AsyncIOMotorClient('mongodb://localhost:27017/?replicaSet=qenaRS')
# client = AsyncIOMotorClient('mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0')
database = client['your_database']
collection = database['your_collection']

def with_transaction(func):
    async def wrapper(*args, **kwargs):
        try:
            async with await client.start_session() as session:
                async with session.start_transaction():
                    # kwargs['session'] = session
                    kwargs['session'] = session
                    result = await func(*args, **kwargs)
                    return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")
    return wrapper

@app.post("/your_transactional_endpoint")
async def your_transactional_endpoint(page: int = 1):
    document_1 = {"name": "Doc1"}
    document_2 = {"name": "Doc2"}
    return await transaction(document_1=document_1, document_2=document_2)

@with_transaction
async def transaction(document_1: dict, document_2: dict, session=None):
    try:
        # result_1 = await collection.insert_one(document_1, session=session)
        result_1 = await sub_transaction_insert(document_1=document_1)
        result_2 = await sub_transaction_insert(document_1=document_2)
        # raise Exception("Exception Happend")
        result_3 = await sub_transaction_update(document_1=document_1)

        if result_1.inserted_id and result_2.inserted_id:
            return {"message": "Both documents inserted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Error: Failed to insert one or both documents")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")

async def sub_transaction_insert(document_1, session=None):
    result_1 = await collection.insert_one(document_1, session=session)
    return result_1

async def sub_transaction_update(document_1, session=None):
    result_1 = await collection.update_one({"_id":ObjectId("65926380cd902176d636983a")},
                                           {
                                               "$set": {
                                                   "name": "65926380cd902176d636983a"
                                               }
                                           },
                                           session=session)
    return result_1

if __name__ == "__main__":
    # uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, workers=2)

