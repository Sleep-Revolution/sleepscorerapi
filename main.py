import json
import os
from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, Response, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time
from Src.Services.AuthenticationService import AuthenticationService
from Src.Services.UploadService import UploadService
from Src.Infrastructure.JWT import JWTBearer, ParseAccessToken
from Src.Models.Models import CentreCreate, AuthCredentials
import ipaddress

from Src.Infrastructure.ErrorMiddleware import ErrorMiddleware

authenticationService = AuthenticationService()
uploadService = UploadService()

app = FastAPI(max_request_size=4*1024*1024*1024) # 4 GB max file size
templates = Jinja2Templates(directory="templates")

jwtBearer = JWTBearer()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    # if exc.status_code == 401:
    return RedirectResponse('/login')
    # return templates.TemplateResponse("error.html", {"request": request, "error": exc})

async def PreprocessRequest(request: Request, call_next):
    request.state.host = request.client.host
    session_id = request.cookies.get("session_id")
    request.state.xforwarded = request.headers.get("X-Forwarded-For")
    if request.state.xforwarded is not None:
        request.state.onVPN = ipaddress.ip_address(request.headers.get("X-Forwarded-For")) in ipaddress.ip_network('192.168.209.0/24')
        request.state.superAdmin = request.headers.get("X-Forwarded-For") in ['10.3.25.191']
    else:
        request.state.onVPN = ipaddress.ip_address(request.client.host) in ipaddress.ip_network('192.168.209.0/24')
        request.state.superAdmin = request.client.host in ['10.3.25.191', '127.0.0.1']
    
    request.state.centre = None
    if not session_id:
        return await call_next(request)
    try:
        id = ParseAccessToken(session_id)
        centre = authenticationService.GetCentreById(id)
        request.state.centre = centre
    except Exception as e:
        return await call_next(request)


    return await call_next(request)
    
app.middleware("http")(PreprocessRequest)

app.add_middleware(ErrorMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    '''This is the root page of our portal, this needs to be replaced with a log-in page.'''
    data = {
        "page": "Login",
    }
    return templates.TemplateResponse("login.html", {"request": request, "data": data})

@app.get('/me')
async def getMyIp(request: Request):
    return {'ip': request.state.host, 'xfw': request.state.xforwarded, "onVpn": request.state.onVPN, "issup": request.state.superAdmin}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    print("this is the centre", request.state.centre)
    data = {
        "page": "Home page",
    }
    return templates.TemplateResponse("index.html", {"request": request, "data": data, "centre": request.state.centre})


@app.post('/uploadfile', response_class=HTMLResponse)
async def create_upload_file(request: Request, file: UploadFile = File(...), recordingNumber: int = Form(...)):
    # centre = authenticationService.GetCentreById(request)
    centre = request.state.centre
    if not centre:
        print("Problem finding centre in request")
        raise ValueError("Centre required.")

    if recordingNumber == -1:
        print("Got invalid recording.")
        raise ValueError("Recording number must be provided.")

    print(recordingNumber, centre.request.state.xforwarded)

    if file.content_type != "application/zip":
        # data = {
        #     "title": "Upload failed",
        #     "status": "failed",
        #     "message": "File type not supported. Please upload a zip file."
        # }
        return RedirectResponse("/upload_complete?success=false&reason=Incorrectfiletype", status_code=302)

    print("->>>> Creating upload")
    # The business logic should be implemented in the service class.
    await uploadService.CreateUpload(centre.Id, file, recordingNumber)

    
    # data = {
    #     "title": "Upload complete",
    #     "status": "success",
    # }
    return RedirectResponse("/upload_complete?success=true", status_code=302)

# @app.post('/')
# async def what(request: Request):
#     return {}

@app.get('/upload_complete', response_class=HTMLResponse)
async def uploadComplete(request: Request,  success: bool = False):
    centre = request.state.centre
    return templates.TemplateResponse("upload_complete.html", {"request": request, "centre": centre, 'success':success})

@app.get('/centres', response_class=JSONResponse)
async def home(request: Request):
    return [user.__dict__ for user in authenticationService.GetAllCentres() ]

@app.post('/centres',  response_class=JSONResponse)
async def CreateCentre(newCentre:  CentreCreate):
    return authenticationService.CreateCentre(newCentre)

@app.post("/authenticate", response_class=JSONResponse)
async def AuthenticateCentre(credentials: AuthCredentials, response: Response):
    token = authenticationService.AuthenticateCentre(credentials) 
    response.set_cookie(key='session_id', value=token)
    # return RedirectResponse(url = "/")

@app.get("/admin", response_class=HTMLResponse)
async def AdminStuff(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        preprocConsumers = len(uploadService.get_active_connections("dev_preprocessing_queue"))
        procConsumers = len(uploadService.get_active_connections("dev_task_queue"))
        return templates.TemplateResponse("Admin/admin.html", {"request": request, "centre": request.state.centre, "preprocConsumers": preprocConsumers, "procConsumers": procConsumers})

@app.get("/admin/uploads", response_class=HTMLResponse)
async def UploadList(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        return templates.TemplateResponse("Admin/uploads.html", {"request": request, "centre": request.state.centre, 'centres': uploadService.GetAllCentres()})

@app.get("/admin/uploads/{id}", response_class=JSONResponse)
async def UploadDetails(request: Request, id: int):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        upload = uploadService.GetUploadById(id)
        nights = uploadService.RescanLocationsForUpload(id)
        return templates.TemplateResponse("Admin/upload.html", {"request": request, "centre": request.state.centre, 'upload': upload, 'scannedNights': nights})

@app.get("/admin/uploads/{id}/scan", response_class=JSONResponse)
async def ScanPage(request: Request, id: int):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        upload = uploadService.GetUploadById(id)
        return templates.TemplateResponse("Admin/upload_scan.html", {"request": request, "centre": request.state.centre, 'upload': upload})
    else:
        return RedirectResponse('/')

@app.post("/admin/upload/{id}/nights", response_class=HTMLResponse)
async def AddNights(id: int, request: Request):
    form_data = await request.form()
    form_data = list(form_data.items())
    if form_data[0][0] != 'centre_id':
        raise ValueError("Incorrect form received for nights.")

    centre_id = form_data[0][1]

    form_data = form_data[1:]
    metadata = list(filter(lambda x: 'metadata' in x[0], form_data))
    qualdata = list(filter(lambda x: x not in metadata, form_data))

    metadata.sort(key = lambda x: x[0])
    qualdata.sort(key = lambda x: x[0])
    
    if len(metadata) != len(qualdata):
        raise ValueError("Incorrect length of metadata and quality data.")

    for md, qd in zip(metadata, qualdata):
        if md[0].split('/')[1] != qd[0].split('/')[1]:
            raise ValueError("Mismatch in tag for quality and metadata in adding nights. ")
        loc = qd[0]
        quality = qd[1]
        mdata = md[1]
        uploadService.addNightToUpload(id, loc, quality, mdata)

    for nightLocation, quality in form_data[1:]:
        # Extract the values for each row
        recording_quality = quality

        # Perform further processing or save the data to a file or database
        # Example:
        print(f"Location: {nightLocation}, Recording Quality: {recording_quality}")
        
    # Optionally, you can redirect the user to a different page after processing the form
    #     return {"message": "You are not admin lmao"}
    # else: 
    #     return {"message": "You are an admin lmao!!!!!!!!!!!!!!!!!!!!!!!!"}
    
    # return RedirectResponse(url = "/")

# @app.get('/upload')
# async def upload(request = Depends(jwtBearer)):
#     return {}

# @app.post('/upload')
# async def upload(file: UploadFile, request = Depends(jwtBearer)):
#     print(file.file.read())
#     print(request)
#     id = str(uuid.uuid4())
#     print(id)

    


# @app.get("/me")
# def protected_route(bla = Depends(jwtBearer)):
#     user = authenticationService.GetCentreById(bla)
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

#     return user


@app.get("/download", response_class=HTMLResponse)
async def home(request: Request=Depends(jwtBearer)):
    data = {
        "page": "Download page",
    }
    return templates.TemplateResponse("download.html", {"request": request, "data": data})
