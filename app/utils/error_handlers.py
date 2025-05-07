from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from typing import Union

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors from FastAPI and return structured error responses
    """
    errors = []
    for error in exc.errors():
        error_msg = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        }
        errors.append(error_msg)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle SQLAlchemy errors and return structured error responses
    """
    error_msg = str(exc)
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        status_code = status.HTTP_400_BAD_REQUEST
        if "UNIQUE constraint failed" in error_msg:
            error_msg = "A record with these details already exists"
        elif "FOREIGN KEY constraint failed" in error_msg:
            error_msg = "Referenced record does not exist"
    
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": "Database error",
            "message": error_msg
        }
    )

async def pydantic_validation_handler(request: Request, exc: ValidationError):
    """
    Handle Pydantic validation errors that occur outside of request validation
    """
    errors = []
    for error in exc.errors():
        error_msg = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        }
        errors.append(error_msg)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Data validation error",
            "errors": errors
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle any uncaught exceptions and return a friendly error message
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc)
        }
    )