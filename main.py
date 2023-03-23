from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import jwt
from typing import List
import time
from random import randint
import os
from Src.Services.AuthenticationService import AuthenticationService
from Src.Infrastructure.JWT import JWTBearer
from Src.Models.Models import CentreCreate, AuthCredentials


authenticationService = AuthenticationService()


UPLOAD_DIR = "uploaded_files"

app = FastAPI(max_request_size=4*1024*1024*1024) # 4 GB max file size
templates = Jinja2Templates(directory="templates")







jwtBearer = JWTBearer()





app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/centres', response_class=JSONResponse)
async def home(request: Request):
    return [user.__dict__ for user in authenticationService.GetAllCentres() ]

@app.post('/centres',  response_class=JSONResponse)
async def CreateCentre(newCentre:  CentreCreate):
    return authenticationService.CreateCentre(newCentre)

@app.post("/authenticate", response_class=JSONResponse)
async def AuthenticateCentre(credentials: AuthCredentials):
    return authenticationService.AuthenticateCentre(credentials)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = {
        "page": "Home page",
    }
    return templates.TemplateResponse("index.html", {"request": request, "data": data})

@app.get("/me")
def protected_route(bla = Depends(jwtBearer)):
    user = authenticationService.GetCentreById(1)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


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
    
