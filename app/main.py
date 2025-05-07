from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.database.db import engine
from app.models.user import Base as UserBase
from app.models.transaction import Base as TransactionBase
from app.models.category import Base as CategoryBase
from app.models.budget import Base as BudgetBase
from app.routes.users import router as users_router
from app.routes.transactions import router as transactions_router
from app.routes.auth import router as auth_router
from app.routes.categories import router as categories_router
from app.routes.budgets import router as budgets_router
from app.routes.reports import router as reports_router
from app.utils.error_handlers import (
    validation_exception_handler,
    sqlalchemy_exception_handler, 
    pydantic_validation_handler,
    general_exception_handler
)
from app.utils.rate_limiter import rate_limiter

# Create database tables
UserBase.metadata.create_all(bind=engine)
TransactionBase.metadata.create_all(bind=engine)
CategoryBase.metadata.create_all(bind=engine)
BudgetBase.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Personal Finance API",
    description="""
    A comprehensive API for personal finance management.
    
    Features:
    - User authentication with JWT
    - Transaction tracking and categorization
    - Budget management
    - Financial reports and analytics
    
    All endpoints require authentication except for user registration and login.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Operations related to user authentication"
        },
        {
            "name": "users",
            "description": "Operations related to user management"
        },
        {
            "name": "categories",
            "description": "Operations related to transaction categories"
        },
        {
            "name": "transactions",
            "description": "Operations related to financial transactions"
        },
        {
            "name": "budgets",
            "description": "Operations related to budget management"
        },
        {
            "name": "reports",
            "description": "Financial reports and analytics"
        }
    ]
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_handler)
app.add_exception_handler(Exception, general_exception_handler)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Personal Finance API!"}

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(budgets_router)
app.include_router(transactions_router)
app.include_router(reports_router)

@app.middleware("http")
async def validate_responses(request: Request, call_next):
    """
    Middleware to validate all responses against their declared models
    """
    response = await call_next(request)
    
    # Add additional validation here if needed
    
    return response

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    if rate_limiter.is_rate_limited(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    return await call_next(request)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time information to all responses"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response