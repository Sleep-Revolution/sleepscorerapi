from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    status_code = 400  # Default status code for a Bad Request
    if str(exc) == "Some specific condition":  # Customize based on your requirements
        status_code = 412  # Precondition Failed
    return JSONResponse({"error": str(exc)}, status_code=status_code)

class ErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except ValueError as exc:
            response = value_error_handler(request, exc)
        return response