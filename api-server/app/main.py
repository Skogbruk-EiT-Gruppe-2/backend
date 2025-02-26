from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.models import *
from app.db import db
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
import os

def convert_objectid(doc):
    """Recursively converts ObjectId fields to strings in a document."""
    if isinstance(doc, list):
        return [convert_objectid(d) for d in doc]
    if isinstance(doc, dict):
        return {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
    return doc

app = FastAPI()

origins = [
    "*", # Allow all origins
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Get logs from the database (with pagination, sorted by "received" timestamp)
@app.get("/logs")
async def get_logs(page: int = 1, limit: int = 10):
    collection = db["logs"]
    results = collection.find().sort("received", -1).skip((page - 1) * limit).limit(limit)
    result_list = list(results)
    return convert_objectid(result_list)

@app.post("/span/webhook")
async def receive_span_messages(body: dict):
    print(body)

    # Validate the body
    # try:
    #     WebhookPayload.model_validate(body)
    # except ValidationError as e:
    #     # Return a 422 response if the body is invalid
    #     return JSONResponse(status_code=422, content={"error": "Could not validate request body"})

    messages = body["messages"]
    db['logs'].insert_many(messages)
    print("Inserted messages into logs collection")
    return

# Upload an audio file as a blob (array of uint8)
@app.post("/upload-audio")
async def upload_audio_file(request: Request):
    body = await request.body()

    print(f"Received {len(body)} bytes")
    print(body)

    # Get the first bytes as the imsi of the device
    imsi = body[:15].decode("utf-8")
    print(f"IMSI: {imsi}")

    # Get the next 2 bytes as the file number (unsigned int16)
    file_number = int.from_bytes(body[15:17], "big")
    print(f"File number: {file_number}")

    # Get the next 2 bytes as the sequence number (unsigned int16)
    sequence_number = int.from_bytes(body[17:19], "big")
    print(f"Sequence number: {sequence_number}")

    # Get the rest of the bytes as the audio blob
    blob = body[17:]

    # Check for an end of file marker (0xFF 0xD9)
    eof_marker = b"\xFF\xD9"
    is_last_blob = False
    if blob.endswith(eof_marker):
        # print("End of file marker found")
        blob = blob[:-2]
        is_last_blob = True
    else:
        # print("End of file marker not found")
        pass

    # Save the blob to a file under the audio_files directory under the IMSI directory (create if not exists)
    # Save in the 'segmented/{file_number}' directory for later reconstruction
    # Use name format: '{sequence_number}.bin'
    # Create the directories if they do not exist
    directory = f"audio_files/{imsi}/segmented/{file_number}"
    os.makedirs(directory, exist_ok=True)
    file_path = f"{directory}/{sequence_number}.bin"
    with open(file_path, "wb") as file:
        file.write(blob)
    print(f"Saved blob to {file_path}")

    if is_last_blob:
        # Combine all the blobs into a single file and save it under the 'audio_files/{imsi}' directory
        # Name format: '{file_number}.bin'
        combined_file_path = f"audio_files/{imsi}/{file_number}.bin"
        with open(combined_file_path, "wb") as file:
            for i in range(sequence_number + 1):
                segment_path = f"audio_files/{imsi}/segmented/{file_number}/{i}.bin"
                with open(segment_path, "rb") as segment_file:
                    segment = segment_file.read()
                    file.write(segment)

        print(f"Combined all segments into {combined_file_path}")

    return {"message": "Audio file uploaded successfully"}