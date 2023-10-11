from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, Response, Form, Cookie, Query
from Src.Infrastructure.JWT import ParseAccessToken
from Src.Services.AuthenticationService import AuthenticationService
import ipaddress

async def PreprocessRequest(request: Request, call_next):
    authenticationService = AuthenticationService()
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
