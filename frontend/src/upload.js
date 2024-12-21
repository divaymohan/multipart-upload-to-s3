import React, { useState } from "react";
import axios from "axios";

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [fileUrl, setFileUrl] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleFileUpload = async () => {
    const fileName = file.name;
    const fileType = file.type;
    let uploadId = "";
    let parts = [];

    try {
      // Start the multipart upload
      const startUploadResponse = await axios.post(
        "http://localhost:8000/start-upload",
        {
          fileName,
          fileType,
        },
        {
            headers: {
              "Content-Type": "application/json",
            },
          }
        
      );

      uploadId = startUploadResponse.data.uploadId;

      // Split the file into chunks and upload each part
      const totalParts = Math.ceil(file.size / CHUNK_SIZE);

      console.log(totalParts);

      for (let partNumber = 1; partNumber <= totalParts; partNumber++) {
        const start = (partNumber - 1) * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const fileChunk = file.slice(start, end);

        const reader = new FileReader();
        reader.readAsArrayBuffer(fileChunk);

        const uploadPart = () => {
          return new Promise((resolve, reject) => {
            reader.onload = async () => {
              const fileChunkBase64 = btoa(
                new Uint8Array(reader.result).reduce(
                  (data, byte) => data + String.fromCharCode(byte),
                  ""
                )
              );

              const uploadPartResponse = await axios.post(
                "http://localhost:8000/upload-part",
                {
                  fileName,
                  partNumber,
                  uploadId,
                  fileChunk: fileChunkBase64,
                }
              );

              parts.push({
                ETag: uploadPartResponse.data.ETag,
                PartNumber: partNumber,
              });
              resolve();
            };
            reader.onerror = reject;
          });
        };

        await uploadPart();
      }

      // Complete the multipart upload
      const completeUploadResponse = await axios.post(
        "http://localhost:8000/complete-upload",
        {
          fileName,
          uploadId,
          parts,
        }
      );

      setFileUrl(completeUploadResponse.data.fileUrl);
      alert("File uploaded successfully");
    } catch (error) {
      console.error("Error uploading file:", error);
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button disabled={!file} onClick={handleFileUpload}>
        Upload
      </button>
      <hr />
      <br />
      <br />
      {fileUrl && (
        <a href={fileUrl} target="_blank" rel="noopener noreferrer">
          View Uploaded File
        </a>
      )}
    </div>
  );
};

export default FileUpload;