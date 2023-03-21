from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List
import time
from random import randint
import os

UPLOAD_DIR = "uploaded_files"

app = FastAPI(max_request_size=4*1024*1024*1024) # 4 GB max file size
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = {
        "page": "Home page",
    }
    return templates.TemplateResponse("index.html", {"request": request, "data": data})

@app.get("/download", response_class=HTMLResponse)
async def home(request: Request):
    data = {
        "page": "Download page",
    }
    return templates.TemplateResponse("download.html", {"request": request, "data": data})

@app.post('/uploadfile', response_class=HTMLResponse)
async def create_upload_file(request: Request, file: UploadFile):
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    if file.content_type != "application/zip":
        data = {
            "title": "Upload failed",
            "status": "failed",
            "message": "File type not supported. Please upload a zip file."
        }
        return templates.TemplateResponse("upload_complete.html", {"request": request, "data": data})
    file_location = f'{UPLOAD_DIR}/{file.filename}'
    with open(file_location, 'wb+') as file_object:
        file_object.write(file.file.read())
    time.sleep(3)
    # TODO: Run pipeline steps

    data = {
        "title": "Upload complete",
        "status": "success",
    }
    return templates.TemplateResponse("upload_complete.html", {"request": request, "data": data})
    
