import base64

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import boto3
import os
from typing import List

from starlette.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with the specific domain(s) of your frontend if possible
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

BUCKET = "test-dm-test"

# Initialize S3 client
s3 = boto3.client('s3')  # Replace "your-region" with your AWS region


# Define request body models
class StartUploadRequest(BaseModel):
    fileName: str
    fileType: str


class CompleteUploadRequest(BaseModel):
    fileName: str
    uploadId: str
    parts: List[dict]


@app.post("/start-upload")
async def start_upload(request: StartUploadRequest):
    print(request.model_dump())
    params = {
        "Bucket": BUCKET,
        "Key": request.fileName,
        "ContentType": request.fileType,
    }

    try:
        response = s3.create_multipart_upload(**params)
        print(response)
        return {"uploadId": response["UploadId"]}
    except Exception as error:
        print(error)
        raise HTTPException(status_code=500, detail=str(error))

class UploadPartRequest(BaseModel):
    fileName: str
    partNumber: int
    uploadId: str
    fileChunk: str


@app.post("/upload-part")
async def upload_part(
        upload_file: UploadPartRequest
):
    try:
        print(upload_file.fileName)
        print(upload_file.partNumber)
        print(upload_file.uploadId)
        # Read the file chunk and encode as binary
        file_chunk = base64.b64decode(upload_file.fileChunk)
        params = {
            "Bucket": BUCKET,
            "Key": upload_file.fileName,
            "PartNumber": upload_file.partNumber,
            "UploadId": upload_file.uploadId,
            "Body": file_chunk,
        }

        # Upload the part to S3
        response = s3.upload_part(**params)
        return {"ETag": response["ETag"]}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/complete-upload")
async def complete_upload(request: CompleteUploadRequest):
    params = {
        "Bucket": BUCKET,
        "Key": request.fileName,
        "UploadId": request.uploadId,
        "MultipartUpload": {
            "Parts": request.parts,
        },
    }

    try:
        # Complete the multipart upload
        response = s3.complete_multipart_upload(**params)
        return {"fileUrl": response["Location"]}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)