import datetime
import json
from fastapi import APIRouter
from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, Response, Form, Cookie, Query
import humanfriendly
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from Src.Infrastructure.PreprocessRequest import PreprocessRequest

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


from Src.Services.AuthenticationService import AuthenticationService
from Src.Services.AnalyticsService import AnalyticsService

from Src.Services.UploadService import UploadService

from Src.Infrastructure.Utils import format_last_logged_in



authenticationService = AuthenticationService()
uploadService = UploadService()
analyticsService = AnalyticsService()

AdminRouter = FastAPI(   )

@AdminRouter.get("/foo")
async def update_admin(request: Request):
    print(request.state.centre)
    return {"message": "Admin getting schwifty"}

@AdminRouter.get("/account/{id}", response_class=HTMLResponse)
async def GetAccount(request: Request, id:int):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        account = authenticationService.GetCentreById(id)
        return templates.TemplateResponse("Admin/account.html", {"request": request, "centre": request.state.centre, "account": account })

@AdminRouter.post("/reset-password/{account_id}", response_class=RedirectResponse)
async def ChangePassword(
    request: Request,
    account_id: int,
    NewPassword: str = Form(...),
    ConfirmPassword: str = Form(...)
):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login', status_code=302)
    if request.state.centre.IsAdministrator:
        # Validate old password, then update password if old password is correct
        # Use the account_id to locate the account in the database
        # Check if OldPassword matches the stored password hash
        # If yes, update the password to NewPassword
        authenticationService.UpdateCentrePassword(account_id, NewPassword)

        return RedirectResponse(f'/admin/account/{account_id}', status_code=302)
    else:
        return RedirectResponse('/', status_code=302)
        

@AdminRouter.get("/", response_class=HTMLResponse)
async def AdminStuff(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        feed = uploadService.GetLastNUploads(10)
        for upload in feed:
            time_difference = datetime.datetime.now() - upload.Timestamp
            upload.time_since = humanfriendly.format_timespan(time_difference)
        preprocConsumers = len(uploadService.get_active_connections("dev_preprocessing_queue"))
        procConsumers = len(uploadService.get_active_connections("dev_task_queue"))

        breakdown = uploadService.GetUploadsByCenters()

        return templates.TemplateResponse("Admin/admin.html", {"request": request, "centre": request.state.centre, "preprocConsumers": preprocConsumers, "procConsumers": procConsumers, "feed": feed, "breakdown": breakdown}) 

@AdminRouter.get("/uploads", response_class=HTMLResponse)
async def UploadList(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        return templates.TemplateResponse("Admin/uploads.html", {"request": request, "centre": request.state.centre, 'centres': uploadService.GetAllCentres()})
    else:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    
@AdminRouter.get("/dataset", response_class=HTMLResponse)
async def UploadList(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        return templates.TemplateResponse("Admin/dataset.html", {"request": request, "centre": request.state.centre, 'centres': uploadService.GetAllCentres()})
    else:
        print("redirecting due to no creds")
        return RedirectResponse('/login')



@AdminRouter.get("/datasets", response_class=HTMLResponse)
async def GetAllDatasets(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        ldatasets = uploadService.listDatasets()
        return templates.TemplateResponse("Admin/datasets.html", {"request": request, "centre": request.state.centre, "datasets": ldatasets })

@AdminRouter.get("/dataset/{name}", response_class=HTMLResponse)
async def GetAllDatasets(request: Request, name:str):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        recordings = uploadService.listDataset(name)
        return templates.TemplateResponse("Admin/datasetview.html", {"request": request, "centre": request.state.centre, "datasetName": name, "recordings": recordings })


@AdminRouter.post("/dataset/{name}", response_class=HTMLResponse)
async def CreateJobsForDataset(request:Request, name:str):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        uploadService.CreateJobsForDataset(name)
        return templates.TemplateResponse(f"admin/dataset/{name}", {"request": request})
    else:
        return RedirectResponse('/', status_code=302)

@AdminRouter.get("/uploads/{id}", response_class=JSONResponse)
async def UploadDetails(request: Request, id: int):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login', status_code=302)
    if request.state.centre.IsAdministrator:
        upload = uploadService.GetUploadById(id)
        # nights = uploadService.RescanLocationsForUpload(id)
        return templates.TemplateResponse("Admin/upload.html", {"request": request, "centre": request.state.centre, 'upload': upload})

# @AdminRouter.get("/uploads/{id}/scan", response_class=JSONResponse)
# async def ScanPage(request: Request, id: int):
#     if not request.state.centre:
#         print("redirecting due to no creds")
#         return RedirectResponse('/login', status_code=302)
#     if request.state.centre.IsAdministrator:
#         upload = uploadService.GetUploadById(id)
#         return templates.TemplateResponse("Admin/upload_scan.html", {"request": request, "centre": request.state.centre, 'upload': upload})
#     else:
#         return RedirectResponse('/', status_code=302)

@AdminRouter.get("/accounts", response_class=JSONResponse)
async def GetAllAccounts(request: Request):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login')
    if request.state.centre.IsAdministrator:
        accounts = authenticationService.GetAllCentres()
        requestTime = datetime.datetime.now()
        for acc in accounts:
            acc.formatted_last_login = format_last_logged_in(acc.LastLogin, requestTime)

        accounts.sort(key=lambda acc: (acc.Prefix, acc.MemberNumber))

        return templates.TemplateResponse("Admin/accounts.html", {"request": request, "centre": request.state.centre, 'accounts': accounts, "RequestTime": requestTime })

@AdminRouter.post("/add-account", response_class=RedirectResponse)
async def AddAccount(request: Request,  
    CentreName: str = Form(...), Prefix: str = Form(...), MemberNumber: int = Form(...),
    ResponsibleEmail: str = Form(...), Description: str = Form(...),
    Password1: str = Form(...), Password2: str = Form(...)):
    # huhh = e
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login', status_code=302)
    if request.state.centre.IsAdministrator:
        # code will go here.
        authenticationService.CreateCentre(CentreName, Prefix, MemberNumber, ResponsibleEmail, Description, Password1, Password2)
        return RedirectResponse('/admin/accounts', status_code=302)

@AdminRouter.post('/edit-account/{centreId}', response_class=RedirectResponse)
async def AddAccount(request: Request, centreId: int,
    CentreName: str = Form(...), 
    Prefix: str = Form(...), 
    MemberNumber: int = Form(...),
    ResponsibleEmail: str = Form(...), 
    Description: str = Form(...)):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login', status_code=302)
    if not request.state.centre.IsAdministrator:
        return RedirectResponse('/', status_code=302)
        # code will go here.
    authenticationService.UpdateCentre(centreId, CentreName, Prefix, MemberNumber, ResponsibleEmail, Description)
    return RedirectResponse('/admin/accounts', status_code=302)

@AdminRouter.delete("/delete-upload/{uploadId}", response_class=RedirectResponse)
async def DeleteUpload(request: Request, uploadId: int):
    if not request.state.centre:
        print("redirecting due to no creds")
        return RedirectResponse('/login', status_code=302)
    if not request.state.centre.IsAdministrator:
        return RedirectResponse('/', status_code=302)
        # code will go here.
    uploadService.DeleteUpload(uploadId)
    # redirect the user back to the uploads page, with a get request.
    return RedirectResponse('/admin/uploads', status_code=302)