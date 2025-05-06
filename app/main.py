from fastapi import FastAPI
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

# Create database tables
UserBase.metadata.create_all(bind=engine)
TransactionBase.metadata.create_all(bind=engine)
CategoryBase.metadata.create_all(bind=engine)
BudgetBase.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(title="Personal Finance API")

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