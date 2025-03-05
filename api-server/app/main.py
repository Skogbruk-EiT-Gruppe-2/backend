from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from pydantic import ValidationError
from app.models import *
from app.db import db
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
import os
from app.analysis import process_audio_file

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
async def get_observations(from_date: str = None):
    collection = db["observations"]
    results = collection.find({"timestamp": {"$gte": datetime.fromisoformat(from_date)}}) if from_date else collection.find()
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
async def upload_audio_file(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.body()

        # Get the IMSI from the X-IMSI header
        imsi = request.headers["X-IMSI"]

        # Get the sequence number from the X-Sequence-Number header
        sequence_number = int(request.headers["X-Sequence-Number"])

        # Get the file ID from the X-File-ID header
        file_id = request.headers["X-File-ID"]

        # Get end of file (true/false) from the X-End-Of-File header
        end_of_file = request.headers["X-End-Of-File"]
        # Check if this is the last blob in the sequence
        is_last_blob = end_of_file == "true"

        # Get the blob from the request body
        blob = body

        # Save the blob to a file under the audio_files directory under the IMSI directory (create if not exists)
        # Save in the 'segmented/{file_number}' directory for later reconstruction
        # Use name format: '{sequence_number}.bin'
        # Create the directories if they do not exist
        directory = f"audio_files/{imsi}/segmented/{file_id}"
        os.makedirs(directory, exist_ok=True)
        file_path = f"{directory}/{sequence_number}.bin"
        with open(file_path, "wb") as file:
            file.write(blob)
        print(f"Saved blob to {file_path}")

        is_first_blob = sequence_number == 0
        if is_first_blob:
            # Get device information from the database
            collection = db["devices"]
            device = collection.find_one({"imsi": imsi})
            if device is not None:
                latitude = device["latitude"]
                longitude = device["longitude"]
            else:
                latitude = None
                longitude = None

            # Create entry in the database for the observation
            observation = {
                "_id": file_id,
                "imsi": imsi,
                "value": {
                    "classification": None,
                    "is_redlisted": None,
                },
                "timestamp": datetime.now(),
                "latitude": latitude,
                "longitude": longitude,
                "file_path": None
            }

            collection = db["observations"]
            collection.insert_one(observation)
            print(f"Created observation for {imsi} with ID {file_id}")

        if is_last_blob:
            # Combine all the blobs into a single file and save it under the 'audio_files/{imsi}' directory
            # Name format: '{file_number}.wav'
            # Get the sample rate and bits per sample from the headers of the request (X-Sample-Rate and X-Bits-Per-Sample)
            sample_rate = int(request.headers["X-Sample-Rate"])
            bits_per_sample = int(request.headers["X-Bits-Per-Sample"])

            # Assume mono audio for now
            channels = 1

            # Combine the segmented files into a single file
            combined_file_path = f"audio_files/{imsi}/{file_id}.wav"
            with open(combined_file_path, "wb") as file:
                
                # Write the WAV header
                # https://docs.fileformat.com/audio/wav/
                # RIFF header
                file.write(b"RIFF")
                # File size (filled in later)
                file.write(b"\x00\x00\x00\x00")
                # WAVE header
                file.write(b"WAVE")
                # fmt subchunk
                file.write(b"fmt ")
                # Subchunk size (16 for PCM)
                file.write(b"\x10\x00\x00\x00")
                # Audio format (1 for PCM)
                file.write(b"\x01\x00")
                # Number of channels
                file.write(channels.to_bytes(2, "little"))
                # Sample rate
                file.write(sample_rate.to_bytes(4, "little"))
                # Byte rate
                byte_rate = sample_rate * channels * bits_per_sample // 8
                file.write(byte_rate.to_bytes(4, "little"))
                # Block align
                block_align = channels * bits_per_sample // 8
                file.write(block_align.to_bytes(2, "little"))
                # Bits per sample
                file.write(bits_per_sample.to_bytes(2, "little"))
                # data subchunk
                file.write(b"data")
                # Subchunk size (filled in later)
                file.write(b"\x00\x00\x00\x00")

                # Print header for debugging
                print(f"Wrote WAV header for {sample_rate} Hz, {bits_per_sample} bits per sample, {channels} channels")

                # Write the audio data (PCM)
                for i in range(sequence_number + 1):
                    segment_path = f"audio_files/{imsi}/segmented/{file_id}/{i}.bin"
                    with open(segment_path, "rb") as segment_file:
                        segment = segment_file.read()
                        file.write(segment)

                # Fill in the file size and data size in the header
                file_size = os.path.getsize(combined_file_path) - 8
                data_size = os.path.getsize(combined_file_path) - 44
                with open(combined_file_path, "r+b") as file:
                    file.seek(4)
                    file.write(file_size.to_bytes(4, "little"))
                    file.seek(40)
                    file.write(data_size.to_bytes(4, "little"))

            print(f"Combined all segments into {combined_file_path}")

            background_tasks.add_task(process_audio_file, combined_file_path, db, file_id)

        return {"message": "Audio file uploaded successfully"}
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": "An error occurred while processing the audio file"})
    
@app.get("/audio_files/{imsi}/{file_id}")
async def get_audio_file(imsi: str, file_id: str):
    print(f"GET /audio_files/{imsi}/{file_id}")
    file_path = f"audio_files/{imsi}/{file_id}.wav"
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(file_path)