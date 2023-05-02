from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time
from Src.Services.AuthenticationService import AuthenticationService
from Src.Services.UploadService import UploadService
from Src.Infrastructure.JWT import JWTBearer, ParseAccessToken
from Src.Models.Models import CentreCreate, AuthCredentials

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
    return {'ip': request.state.host, 'xfw': request.state.xforwarded}


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
async def create_upload_file(file: UploadFile = File(...), request: Request = Depends(jwtBearer)):

    centre = authenticationService.GetCentreById(request)
    

    if file.content_type != "application/zip":
        data = {
            "title": "Upload failed",
            "status": "failed",
            "message": "File type not supported. Please upload a zip file."
        }
        return templates.TemplateResponse("upload_complete.html", {"request": request, "data": data})

    # The business logic should be implemented in the service class.
    uploadService.CreateUpload(centre.Id, file)

    
    data = {
        "title": "Upload complete",
        "status": "success",
    }
    return templates.TemplateResponse("upload_complete.html", {"request": request, "data": data})

# @app.post('/')
# async def what(request: Request):
#     return {}

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

@app.get("/admin")
async def AdminStuff(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if not request.state.centre.IsAdministrator:
        return {"message": "You are not admin lmao"}
    else: 
        return {"message": "You are an admin lmao!!!!!!!!!!!!!!!!!!!!!!!!"}
    
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
