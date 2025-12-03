import os
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from rag_engine import RAGService

app = FastAPI()

# Initialize RAG Service
rag_service = RAGService()

class ChatRequest(BaseModel):
    message: str
    top_k: int = 5
    temperature: float = 0.7
    evaluate: bool = False  # Enable RAG evaluation

class IngestRequest(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 200

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    uploaded_files = []
    for file in files:
        file_path = os.path.join(rag_service.data_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_files.append(file.filename)
    
    return {"message": f"Successfully uploaded {len(uploaded_files)} files", "files": uploaded_files}

@app.post("/ingest")
async def ingest_documents(request: IngestRequest = IngestRequest()):
    try:
        result = rag_service.ingest_folder(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = rag_service.query(
            request.message,
            top_k=request.top_k,
            temperature=request.temperature,
            evaluate=request.evaluate
        )
        return {
            "response": result["answer"],
            "sources": result["sources"],
            "evaluation": result.get("evaluation", None)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files():
    try:
        files = os.listdir(rag_service.data_dir)
        return {"files": files}
    except Exception as e:
        return {"files": []}

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    try:
        file_path = os.path.join(rag_service.data_dir, filename)
        
        # Security check: Ensure the file is within the data directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(rag_service.data_dir)):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(file_path)
        return {
            "message": f"Successfully deleted {filename}",
            "recommendation": "Please re-process documents to update the index"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
