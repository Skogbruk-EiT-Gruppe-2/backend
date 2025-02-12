import requests
from os import environ
from db import db
import time

INTERVAL_S = 300
BATCH_SIZE = 10

api_token = environ("SPAN_API_TOKEN")
collection_id = environ("SPAN_COLLECTION_ID")

API_HOST = "https://api.lab5e.com/span"

headers = {
    "X-API-Token": api_token
}

def get_blobs_metadata(limit):
    blobs_endpoint = f"{API_HOST}/span/collections/{collection_id}/blobs?limit={str(limit)}"

    response = requests.get(blobs_endpoint, headers=headers)
    
    if response.status_code == 200:
        blobs = response["blobs"]
        return blobs
    else:
        return []

def extract(blob):
    blob_id = blob["blobId"]
    created_at: int = blob["created"]

    blob_url = f"{API_HOST}/collections/{collection_id}/blobs/{blob_id}"
    response = requests.get(blob_url, headers=headers, stream=True)

    if response.status_code == 200:
        output_file = f"./data/{str(created_at)}"
        with open(output_file, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"File saved as {output_file}")
        return output_file
    else:
        print(f"Error: {response.status_code} - {response.text}")

def analyse(file_path: str):
    pass

def store_analysis(analysis):
    pass

def process(limit: int):
    blobs_metadata = get_blobs_metadata(limit)

    for blob in blobs_metadata:
        file_path = extract(blob)
        analysis = analyse(file_path)
        store_analysis(analysis)

def main():
    while True:
        time.sleep(INTERVAL_S)
        process(BATCH_SIZE)

if __name__ == "__main__":
    main()
