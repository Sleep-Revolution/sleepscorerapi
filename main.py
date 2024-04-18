import json
import os
from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, Response, Form, Cookie, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time
import datetime
from Src.Services.AuthenticationService import AuthenticationService
from Src.Services.AnalyticsService import AnalyticsService

from Src.Services.UploadService import UploadService
from Src.Infrastructure.JWT import JWTBearer, ParseAccessToken
from Src.Models.Models import CentreCreate, AuthCredentials, NightLogEntity, UploadLogEntity
import ipaddress
from Src.Infrastructure.Utils import format_last_logged_in
from Src.Infrastructure.ErrorMiddleware import ErrorMiddleware
import base64
from Src.Infrastructure.PreprocessRequest import PreprocessRequest

authenticationService = AuthenticationService()
uploadService = UploadService()
analyticsService = AnalyticsService()

app = FastAPI(max_request_size=4*1024*1024*1024) # 4 GB max file size
templates = Jinja2Templates(directory="templates")


from AdminRouter import AdminRouter



jwtBearer = JWTBearer()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    # if exc.status_code == 401:
    # check if request has a header with value 2
    return RedirectResponse('/login')


app.middleware("http")(PreprocessRequest)
AdminRouter.middleware("http")(PreprocessRequest)

app.add_middleware(ErrorMiddleware)
AdminRouter.add_middleware(ErrorMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount('/admin', AdminRouter)




@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    data = {
        "page": "Login",
    }
    return templates.TemplateResponse("login.html", {"request": request, "data": data})

@app.post("/authenticate", response_class=JSONResponse)
async def AuthenticateCentre(credentials: AuthCredentials, response: Response):
    token = authenticationService.AuthenticateCentre(credentials) 
    response.set_cookie(key='session_id', value=token)
    # return RedirectResponse(url = "/")

@app.get("/logout", response_class=RedirectResponse)
async def logout():
    # Clear the session cookie
    response = RedirectResponse(url="/login")  # Adjust the URL as needed
    response.delete_cookie(key="session_id")
    return response

@app.get('/me')
async def getMyIp(request: Request):
    return {'ip': request.state.host, 'xfw': request.state.xforwarded, "onVpn": request.state.onVPN, "issup": request.state.superAdmin}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
        
    uploads = uploadService.getAllUploadsForCentre(request.state.centre.Id)
    data = {
        "page": "Home page",
    }
    return templates.TemplateResponse("index.html", {"request": request, "data": data, "centre": request.state.centre, "uploads":uploads})


def tagize(success, reason):
    debugInfo = {"success":success, "reason": reason}
    s = json.dumps(debugInfo)
    return base64.b64encode(s.encode('ascii')).decode("ascii")
def detag(tag):
    base64_bytes = tag.encode("ascii")
    sample_string_bytes = base64.b64decode(base64_bytes)
    sample_string = sample_string_bytes.decode("ascii")
    return json.loads(sample_string)

@app.post('/uploadfile', response_class=HTMLResponse)
async def create_upload_file(request: Request, file: UploadFile = File(...), 
        recordingNumber: int = Form(...),
        isFollowup: bool = Form(...)
    ):
    # centre = authenticationService.GetCentreById(request)
    centre = request.state.centre
    if not centre: 
        print("Problem finding centre in request")
        dbi = tagize(False, "This upload is not authorized (credentials not found).")
        return RedirectResponse(f"/upload_complete?tag={dbi}", status_code=302)

    if recordingNumber == -1:
        print("Got invalid recording.")
        dbi = tagize(False, "Invalid recording number.")
        return RedirectResponse(f"/upload_complete?tag={dbi}", status_code=302)

    print(recordingNumber, centre.Id, request.state.xforwarded, isFollowup)

    allowedFileTypes = ["application/zip", "application/x-zip-compressed"]
    if file.content_type not in allowedFileTypes:
        print("Invalid file")
        dbi = tagize(False, "Invalid file type.")
        return RedirectResponse(f"/upload_complete?tag={dbi}", status_code=302)
        
    else:
        print(f"->>>> Creating upload with {file.filename}")
        # The business logic should be implemented in the service class.
        try:
            await uploadService.CreateUpload(centre.Id, file, recordingNumber, isFollowup)
        except Exception as e:
            print(e)
            dbi = tagize(False, str(e))
            return RedirectResponse(f"/upload_complete?tag={dbi}", status_code=302)

        dbi = tagize(True, "")
        return RedirectResponse(f"/upload_complete?tag={dbi}", status_code=302)


@app.post("/add-night-to-upload/{uploadId}/{nightNumber}")
async def AddNightToUpload(request:Request, uploadId:int, nightNumber:int):
    print("Adding night to upload", uploadId, nightNumber)
    uploadService.addNightToUpload(uploadId, nightNumber)
    

@app.post("/create-new-job-for-upload/{uploadId}", response_class=JSONResponse)
async def CreateJobForUpload(request:Request, uploadId: int):
    print(uploadId)
    uploadService.createJobForUpload(uploadId)


@app.post('/create-new-job-for-night/{nightId}', response_class=JSONResponse)
async def CreateJobForNight(request:Request, nightId: int):
    uploadService.CreateJobForNight(nightId)
    return {"success": True}

@app.delete('/recording/{recordingId}', response_class=JSONResponse)
async def DeleteRecording(request:Request, recordingId: int):
    if not request.state.superAdmin:
        return {"success": False, "reason": "Not super admin"}
    uploadService.DeleteRecording(recordingId)
    return {"success": True}

@app.get('/uploads', response_class=JSONResponse)
async def GetAllUploadsForCenter(request: Request):

    print(request)
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login', status_code=302)

    return uploadService.getAllUploadsForCentre(request.state.centre.Id)

@app.get('/profile', response_class=HTMLResponse)
async def userProfile(request: Request):
    pass
    
@app.get('/upload_complete', response_class=HTMLResponse)
async def uploadComplete(request: Request,  tag:str = Query("")):
    if tag == "":
        return
    centre = request.state.centre
    debug_info = detag(tag)
    print(debug_info)
    return templates.TemplateResponse("upload_complete.html", {"request": request, "centre": centre, 'success':debug_info['success'], 'reason':debug_info['reason']})

@app.get('/centres', response_class=JSONResponse)
async def home(request: Request):
    return [user.__dict__ for user in authenticationService.GetAllCentres() ]

@app.post('/dataset', response_class=HTMLResponse)
async def create_upload_dataset(request: Request, file: UploadFile = File(...), datasetName: str = Form(...)):
    # centre = authenticationService.GetCentreById(request)
    centre = request.state.centre
    if not centre:
        print("Problem finding centre in request")
        raise ValueError("Centre required.")

    if datasetName == "":
        print("Got invalid dataset name.")
        return RedirectResponse(f"/upload_complete?success=false&reason=Invalid dataset name", status_code=302)
    
    print(datasetName, centre.Id, request.state.xforwarded)

    allowedFileTypes = ["application/zip", "application/x-zip-compressed"]
    if file.content_type not in allowedFileTypes:
        return RedirectResponse(f"/upload_complete?success=false&reason=Incorrectfiletype({file.content_type}, expected {allowedFileTypes})", status_code=302)
    else:
        print(f"->>>> Creating dataset with {datasetName}")
        # The business logic should be implemented in the service class.
        await uploadService.createDataset(file, datasetName)

        return RedirectResponse("/admin/datasets", status_code=302)

@app.post("/meta/log_night")
async def PukeLog(request: Request, log: NightLogEntity):
    analyticsService.AddLogToNight(log)
    
@app.post("/meta/log_upload")
async def PukeLog(request: Request, log: UploadLogEntity):
    analyticsService.AddLogToUpload(log)
    
