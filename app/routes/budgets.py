from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date, datetime

from app.database.db import get_db
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.schemas import BudgetCreate, Budget as BudgetSchema, BudgetStatus
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/budgets",
    tags=["budgets"]
)

@router.post("/", response_model=BudgetSchema)
def create_budget(
    budget: BudgetCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify the category exists and belongs to the user
    category = db.query(Category).filter(
        Category.id == budget.category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if a budget for this category and time period already exists
    existing_budget = db.query(Budget).filter(
        Budget.category_id == budget.category_id,
        Budget.user_id == current_user.id,
        Budget.end_date >= budget.start_date,
        Budget.start_date <= budget.end_date
    ).first()
    
    if existing_budget:
        raise HTTPException(
            status_code=400, 
            detail="A budget for this category and time period already exists"
        )
    
    # Create the budget
    db_budget = Budget(
        amount=budget.amount,
        start_date=budget.start_date or date.today(),
        end_date=budget.end_date,
        category_id=budget.category_id,
        user_id=current_user.id,
        name=budget.name
    )
    
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.get("/", response_model=List[BudgetSchema])
def read_budgets(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only return budgets belonging to the current user
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return budgets

@router.get("/status", response_model=List[BudgetStatus])
def get_budget_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    active_only: bool = True
):
    # Get current date
    today = date.today()
    
    # Base query for budgets
    budget_query = db.query(Budget).filter(Budget.user_id == current_user.id)
    
    # Filter for active budgets if requested
    if active_only:
        budget_query = budget_query.filter(
            Budget.start_date <= today,
            Budget.end_date >= today
        )
    
    # Get all relevant budgets
    budgets = budget_query.all()
    
    # Calculate spending for each budget
    budget_statuses = []
    for budget in budgets:
        # Sum transactions in the budget's category during its time period
        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category_id == budget.category_id,
            func.date(Transaction.date) >= budget.start_date,
            func.date(Transaction.date) <= budget.end_date
        ).scalar() or 0
        
        # Calculate remaining and percentage
        remaining = budget.amount - spent
        percentage_used = (spent / budget.amount * 100) if budget.amount > 0 else 0
        
        # Get category info
        category = db.query(Category).filter(Category.id == budget.category_id).first()
        
        # Create status object
        budget_status = BudgetStatus(
            id=budget.id,
            user_id=budget.user_id,
            amount=budget.amount,
            start_date=budget.start_date,
            end_date=budget.end_date,
            category_id=budget.category_id,
            name=budget.name,
            spent=spent,
            remaining=remaining,
            percentage_used=percentage_used,
            category=category
        )
        
        budget_statuses.append(budget_status)
    
    return budget_statuses

@router.get("/{budget_id}", response_model=BudgetSchema)
def read_budget(
    budget_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

@router.put("/{budget_id}", response_model=BudgetSchema)
def update_budget(
    budget_id: int,
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if db_budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Verify the category exists and belongs to the user
    category = db.query(Category).filter(
        Category.id == budget.category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update budget attributes
    db_budget.amount = budget.amount
    db_budget.start_date = budget.start_date or db_budget.start_date
    db_budget.end_date = budget.end_date
    db_budget.category_id = budget.category_id
    db_budget.name = budget.name
    
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if db_budget is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    db.delete(db_budget)
    db.commit()
    return {"detail": "Budget deleted successfully"}