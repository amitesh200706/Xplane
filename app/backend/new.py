from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import os
import tempfile
import shutil
import uvicorn

from Rag.db_setup import refresh_db 
from Rag.embbed import process_file
from llm import explain_code

class CodeSelection(BaseModel):
    code: str

    startLine: int
    startColumn: int

    endLine: int
    endColumn: int

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8000/upload",
    "http://localhost:8000/response",
    # Add more origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to the FastAPI application!"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    
    suffix = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp:

        contents = await file.read()
        temp.write(contents)

        temp_path = temp.name


    try:
        client = refresh_db()

        chunks_count = process_file(
            temp_path,
            client
        )

        text = contents.decode("utf-8")

        return {
            "filename": file.filename,
            "code": text,
            "chunks_count": chunks_count
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    
@app.post("/response")
async def receive_selection(selection: CodeSelection):
    # Call the LLM function to explain the selected code
    explanation = explain_code(selection.code)
    return {"explanation": explanation}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)