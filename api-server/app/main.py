from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.models import *
from app.db import db
from bson import ObjectId

def convert_objectid(doc):
    """Recursively converts ObjectId fields to strings in a document."""
    if isinstance(doc, list):
        return [convert_objectid(d) for d in doc]
    if isinstance(doc, dict):
        return {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
    return doc

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/observations")
async def get_observations():
    collection = db["observations"]
    results = collection.find()
    result_list = list(results)
    return convert_objectid(result_list)

@app.post("/observations")
async def post_observation(observation: Observation):
    observation_json = jsonable_encoder(observation)

    collection = db["observations"]
    inserted_result = collection.insert_one(observation_json)
    response = {"id": inserted_result.inserted_id}
    return convert_objectid(response)

@app.post("/span/webhook")
async def receive_span_messages(body: dict):
    print(body)

    # Validate the body
    try:
        WebhookPayload.model_validate(body)
    except ValidationError as e:
        # Return a 422 response if the body is invalid
        return JSONResponse(status_code=422, content={"error": "Could not validate request body"})

    messages = body.messages
    db['logs'].insert_many(messages)
    print("Inserted messages into logs collection")
    return